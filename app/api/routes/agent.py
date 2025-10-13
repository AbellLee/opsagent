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
            return await _handle_streaming_chat(session_id, inputs, config)
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


async def _handle_streaming_chat(session_id: UUID, inputs: Dict[str, Any], config: Dict[str, Any]):
    """处理流式模式的聊天 - 使用LangGraph标准流程进行流式输出"""
    import asyncio
    from starlette.responses import StreamingResponse
    
    async def generate_stream():
        """生成SSE流式数据"""

        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        from langgraph.store.postgres.aio import AsyncPostgresStore
        
        async with (
            AsyncPostgresStore.from_conn_string(settings.database_url) as store,
            AsyncPostgresSaver.from_conn_string(settings.database_url) as checkpointer,
        ):
            # 确保检查点表已创建
            await checkpointer.setup()

            # 创建graph实例
            graph = create_graph(checkpointer=checkpointer, store=store)
            
            # 使用异步方式处理graph.stream，直接转发LLM产生的chunk
            async for chunk, metadata in graph.astream(inputs, config, stream_mode="messages"):
                # 检查chunk是否有内容
                if hasattr(chunk, 'content') and chunk.content:
                    # 构造SSE数据
                    chunk_response = ChunkChatCompletionResponse(
                        session_id=str(session_id),
                        chunk=chunk.content,
                        status="streaming",
                        created_at=time.time(),
                        model="tongyi",
                        is_final=False
                    )

                    # 发送SSE数据
                    yield f"data: {chunk_response.model_dump_json()}\n\n"
                    
                    # 稍微延迟以实现打字机效果
                    await asyncio.sleep(0.01)
                
                # 检查是否是结束信号
                elif hasattr(chunk, 'response_metadata') and chunk.response_metadata.get('finish_reason') == 'stop':
                    # 这是结束信号，跳出循环
                    break

    # 返回StreamingResponse，设置正确的SSE headers
    return StreamingResponse(
        generate_stream(),
        media_type="json/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
            "X-Accel-Buffering": "no",  # 禁用nginx缓冲
            "Content-Encoding": "identity"  # 禁用压缩
        }
    )