from fastapi import APIRouter, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, Response
from starlette.responses import Response as StarletteResponse
from starlette.background import BackgroundTask
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal, Iterator
from uuid import UUID
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from app.core.logger import logger
from app.core.config import settings
import json
import time

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore

from typing import Dict, Any
from langchain_core.messages import ToolMessage, AIMessage
from app.agent.graph import create_graph
from app.core.logger import logger

# 导入主应用中的全局实例
router = APIRouter(prefix="/api/sessions", tags=["agent"])

def get_session_messages_from_db(db, session_id: UUID) -> List:
    """从数据库获取会话历史消息"""
    try:
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT role, content, created_at 
            FROM session_messages 
            WHERE session_id = %s 
            ORDER BY created_at ASC
            """,
            (str(session_id),)
        )
        rows = cursor.fetchall()
        
        messages = []
        for row in rows:
            role, content, created_at = row
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
            elif role == "system":
                messages.append(SystemMessage(content=content))
            elif role == "tool":
                messages.append(ToolMessage(content=content, tool_call_id=""))
                
        logger.info(f"从数据库加载了 {len(messages)} 条历史消息")
        return messages
    except Exception as e:
        logger.error(f"获取会话历史消息失败: {e}")
        return []


class AgentExecuteRequest(BaseModel):
    message: str
    tools: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None

class AgentChatRequest(BaseModel):
    message: str
    response_mode: Literal["blocking", "streaming"] = Field(default="blocking", description="响应模式：blocking为阻塞模式，streaming为流式模式")
    tools: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None

# 响应模型
class ChatCompletionResponse(BaseModel):
    """阻塞模式的响应模型"""
    session_id: str
    response: str
    status: str
    created_at: float
    model: str
    usage: Optional[Dict[str, Any]] = None

class ChunkChatCompletionResponse(BaseModel):
    """流式模式的响应块模型"""
    session_id: str
    chunk: str
    status: str
    created_at: float
    model: str
    is_final: bool = False

# 处理函数




@router.post("/{session_id}/execute")
async def execute_agent(
    session_id: UUID,
    request: AgentExecuteRequest,
):
    """执行Agent任务"""
    try:
        # 构造输入
        inputs = {
            "messages": [
                HumanMessage(content=request.message)
            ],
            "user_id": "default_user",  # 实际应用中应从认证信息获取
            "session_id": str(session_id),
            "tool_approval_required": False,
            "pending_tool_approvals": [],
            "intermediate_steps": []
        }
        
        # 按照langgraph规范，使用PostgresSaver作为上下文管理器
        with PostgresSaver.from_conn_string(settings.database_url) as checkpointer:
            # 确保检查点表已创建
            checkpointer.setup()
            # 创建新的agent graph实例
            agent_graph = create_graph(checkpointer=checkpointer)
            # 执行Agent图，并传入检查点配置
            config = {"configurable": {"thread_id": str(session_id)}}
            result = agent_graph.invoke(inputs, config, checkpointer=checkpointer)
        
        # 提取响应消息
        messages = result.get("messages", [])
        if messages:
            last_message = messages[-1]
            return {
                "session_id": session_id,
                "response": last_message.content if hasattr(last_message, 'content') else str(last_message),
                "status": "success"
            }
        else:
            return {
                "session_id": session_id,
                "response": "No response generated",
                "status": "success"
            }
            
    except Exception as e:
        logger.error(f"与Agent聊天失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"与Agent聊天失败: {str(e)}"
        )

@router.post("/{session_id}/chat")
async def chat_with_agent(
    session_id: UUID,
    request: AgentChatRequest,
):
    """与Agent聊天（支持连续对话和流式响应）"""
    try:
        # 检查消息是否为空
        if not request.message or not request.message.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="消息内容不能为空"
            )

        # 构造输入
        inputs = {
            "messages": [
                HumanMessage(content=request.message.strip())
            ],
            "user_id": "default_user",  # 实际应用中应从认证信息获取
            "session_id": str(session_id),
            "tool_approval_required": False,
            "pending_tool_approvals": [],
            "intermediate_steps": []
        }

        # 使用session_id作为thread_id，实现会话级别的记忆
        config = {
            "configurable": {
                "thread_id": str(session_id)
            }
        }

        # 根据响应模式选择处理方式
        if request.response_mode == "streaming":
            return _handle_streaming_chat(session_id, inputs, config)
        else:
            return await _handle_blocking_chat(session_id, inputs, config)

                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"与Agent聊天失败: {str(e)}")
        # 检查是否是数据库连接错误
        error_detail = str(e)
        if "数据库连接失败" in error_detail or "connection to server" in error_detail:
            error_detail = "数据库连接失败，请检查数据库服务是否运行正常"
        # 如果是模型API密钥问题，提供更明确的错误信息
        elif "api key" in error_detail.lower() or "dashscope" in error_detail.lower():
            error_detail = "模型服务未配置：请配置通义千问API密钥(DASHSCOPE_API_KEY)才能使用AI功能"
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"与Agent聊天失败: {error_detail}"
        )

async def _handle_blocking_chat(session_id: UUID, inputs: Dict[str, Any], config: Dict[str, Any]) -> ChatCompletionResponse:
    """处理阻塞模式的聊天 - 使用LangGraph标准流程"""
    try:
        # 按照LangGraph规范，使用PostgresSaver作为上下文管理器
        with (
            PostgresStore.from_conn_string(settings.database_url) as store,
            PostgresSaver.from_conn_string(settings.database_url) as checkpointer,
        ):
            # 确保检查点表已创建
            checkpointer.setup()

            # 创建graph实例
            graph = create_graph(checkpointer=checkpointer, store=store)

            # 执行graph
            result = graph.invoke(inputs, config)

            # 提取响应内容
            messages = result.get("messages", [])
            if messages:
                last_message = messages[-1]
                response_content = last_message.content if hasattr(last_message, 'content') else str(last_message)
            else:
                response_content = "抱歉，没有收到回复。"

            return ChatCompletionResponse(
                session_id=str(session_id),
                response=response_content,
                status="success",
                created_at=time.time(),
                model="tongyi"
            )

    except Exception as e:
        logger.error(f"阻塞聊天失败: {e}")
        raise HTTPException(status_code=500, detail=f"阻塞聊天失败: {str(e)}")

def _handle_streaming_chat(session_id: UUID, inputs: Dict[str, Any], config: Dict[str, Any]) -> StreamingResponse:
    """处理流式模式的聊天 - 使用LangGraph标准流程进行流式输出"""

    def generate_stream():
        """生成SSE流式数据"""
        try:
            # 按照LangGraph规范，使用PostgresSaver作为上下文管理器
            with (
                PostgresStore.from_conn_string(settings.database_url) as store,
                PostgresSaver.from_conn_string(settings.database_url) as checkpointer,
            ):
                # 确保检查点表已创建
                checkpointer.setup()

                # 创建graph实例
                graph = create_graph(checkpointer=checkpointer, store=store)

                # 使用混合方案：在LangGraph框架内直接调用LLM的流式功能
                logger.info(f"开始LangGraph流式处理，会话ID: {session_id}")

                # 获取LLM实例并准备消息（与阻塞模式保持一致的逻辑）
                from app.core.llm import get_llm
                llm, _ = get_llm()

                # 准备消息（包含系统消息和历史消息）
                system_msg = "你是一个智能助手"
                # 这里可以添加从store获取长期记忆的逻辑，与阻塞模式保持一致
                messages = [SystemMessage(content=system_msg)]
                messages.extend(inputs["messages"])

                full_content = ""
                has_content = False

                # 根据模型类型选择合适的调用方式（与graph.py中的逻辑保持一致）
                if hasattr(llm, 'dashscope_api_key') or type(llm).__name__ == 'Tongyi':
                    # 对于Tongyi模型，使用字典格式
                    formatted_messages = []
                    for msg in messages:
                        if isinstance(msg, SystemMessage):
                            formatted_messages.append({"role": "system", "content": msg.content})
                        elif isinstance(msg, HumanMessage):
                            formatted_messages.append({"role": "user", "content": msg.content})
                        elif isinstance(msg, AIMessage):
                            formatted_messages.append({"role": "assistant", "content": msg.content})
                        else:
                            formatted_messages.append({"role": "user", "content": str(getattr(msg, 'content', str(msg)))})

                    # 流式调用Tongyi模型
                    stream = llm.stream(formatted_messages)
                else:
                    # 对于其他模型，使用BaseMessage对象列表
                    stream = llm.stream(messages)

                # 处理流式输出
                for chunk in stream:
                    try:
                        # 提取chunk内容
                        chunk_text = ""
                        if hasattr(chunk, 'content'):
                            chunk_text = chunk.content
                        elif isinstance(chunk, str):
                            chunk_text = chunk
                        elif hasattr(chunk, 'text'):
                            chunk_text = chunk.text
                        else:
                            chunk_text = str(chunk)

                        if chunk_text:
                            full_content += chunk_text
                            has_content = True

                            # 构造SSE数据
                            chunk_response = ChunkChatCompletionResponse(
                                session_id=str(session_id),
                                chunk=chunk_text,
                                status="streaming",
                                created_at=time.time(),
                                model="tongyi",
                                is_final=False
                            )

                            # 发送SSE数据
                            yield f"data: {chunk_response.model_dump_json()}\n\n"

                    except Exception as chunk_error:
                        logger.error(f"处理流式chunk失败: {chunk_error}")
                        continue

                # 保存完整响应到数据库（使用LangGraph的检查点机制）
                if full_content:
                    # 构造完整的AI消息并保存到graph状态
                    ai_message = AIMessage(content=full_content)

                    # 构造包含完整对话的输入，用于保存到检查点
                    save_inputs = inputs.copy()
                    save_inputs["messages"] = inputs["messages"] + [ai_message]

                    # 使用graph.invoke保存最终状态到检查点
                    try:
                        graph.invoke(save_inputs, config)
                        logger.info(f"已保存流式响应到检查点，长度: {len(full_content)} 字符")
                    except Exception as save_error:
                        logger.error(f"保存流式响应到检查点失败: {save_error}")

                # 如果没有接收到任何内容，发送默认消息
                if not has_content:
                    default_response = ChunkChatCompletionResponse(
                        session_id=str(session_id),
                        chunk="抱歉，没有收到回复。",
                        status="streaming",
                        created_at=time.time(),
                        model="tongyi",
                        is_final=False
                    )
                    yield f"data: {default_response.model_dump_json()}\n\n"

                logger.info(f"LangGraph流式处理完成，总长度: {len(full_content)} 字符")

                # 发送最终完成信号
                final_response = ChunkChatCompletionResponse(
                    session_id=str(session_id),
                    chunk="",
                    status="completed",
                    created_at=time.time(),
                    model="tongyi",
                    is_final=True
                )
                yield f"data: {final_response.model_dump_json()}\n\n"

                # 发送结束标记
                yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"流式聊天失败: {e}")
            # 发送错误信息
            error_response = ChunkChatCompletionResponse(
                session_id=str(session_id),
                chunk=f"错误: {str(e)}",
                status="error",
                created_at=time.time(),
                model="tongyi",
                is_final=True
            )
            yield f"data: {error_response.model_dump_json()}\n\n"
            yield "data: [DONE]\n\n"

    # 返回StreamingResponse，设置正确的SSE headers
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )