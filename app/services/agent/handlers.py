"""
Agent服务的核心业务逻辑处理
"""
from typing import Dict, Any
from uuid import UUID
import time
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore

from app.core.logger import logger
from app.core.config import settings
from app.agent.graph import create_graph
from app.services.agent.models import ChatCompletionResponse, ChunkChatCompletionResponse
from app.services.agent.utils import build_agent_inputs, create_agent_config


async def execute_agent_task(session_id: UUID, message: str, tools=None, config=None) -> Dict[str, Any]:
    """执行Agent任务的核心业务逻辑"""
    # 构造输入
    inputs = build_agent_inputs(message, session_id)
    
    # 按照langgraph规范，使用PostgresSaver作为上下文管理器
    with PostgresSaver.from_conn_string(settings.database_url) as checkpointer:
        # 确保检查点表已创建
        checkpointer.setup()
        # 创建新的agent graph实例
        agent_graph = create_graph(checkpointer=checkpointer)
        # 执行Agent图，并传入检查点配置
        config = create_agent_config(session_id)
        result = agent_graph.invoke(inputs, config, checkpointer=checkpointer)
    
    # 提取响应消息 - 只获取最后的AIMessage
    messages = result.get("messages", [])
    response_content = "No response generated"

    # 从后往前查找最后一个AIMessage
    for message in reversed(messages):
        if isinstance(message, AIMessage) and hasattr(message, 'content') and message.content:
            response_content = message.content
            break

    return {
        "session_id": session_id,
        "response": response_content,
        "status": "success"
    }


async def handle_blocking_chat(session_id: UUID, inputs: Dict[str, Any], config: Dict[str, Any]) -> ChatCompletionResponse:
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

        # 提取响应内容 - 只获取最后的AIMessage
        messages = result.get("messages", [])
        response_content = "抱歉，没有收到回复。"

        # 从后往前查找最后一个AIMessage
        for message in reversed(messages):
            if isinstance(message, AIMessage) and hasattr(message, 'content') and message.content:
                response_content = message.content
                break

        return ChatCompletionResponse(
            session_id=str(session_id),
            response=response_content,
            status="success",
            created_at=time.time(),
            model="tongyi"
        )


async def handle_streaming_chat(session_id: UUID, inputs: Dict[str, Any], config: Dict[str, Any]):
    """处理流式模式的聊天 - 使用LangGraph标准流程进行流式输出"""
    
    def generate_stream():
        """生成SSE流式数据"""

        with (
            PostgresStore.from_conn_string(settings.database_url) as store,
            PostgresSaver.from_conn_string(settings.database_url) as checkpointer,
        ):

            # 创建graph实例
            graph = create_graph(checkpointer=checkpointer, store=store)
            
            # 使用异步方式处理graph.stream，直接转发LLM产生的chunk
            # 重要：不要中途break，让LangGraph完整执行以确保状态正确保存
            try:
                stream_finished = False
                for chunk, _ in graph.stream(inputs, config, stream_mode="messages"):
                    # 只处理AIMessage，过滤掉ToolMessage
                    if isinstance(chunk, AIMessage) and hasattr(chunk, 'content') and chunk.content:
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

                    # 检查是否是结束信号，但不要break，让图完整执行
                    elif isinstance(chunk, AIMessage) and hasattr(chunk, 'response_metadata') and chunk.response_metadata.get('finish_reason') == 'stop':
                        # 标记流已结束，但继续让图执行完毕
                        if not stream_finished:
                            stream_finished = True
                            final_response = ChunkChatCompletionResponse(
                                session_id=str(session_id),
                                chunk="",
                                status="completed",
                                created_at=time.time(),
                                model="tongyi",
                                is_final=True
                            )
                            yield f"data: {final_response.model_dump_json()}\n\n"

                # 图执行完毕后，如果还没有发送结束信号，则发送
                if not stream_finished:
                    final_response = ChunkChatCompletionResponse(
                        session_id=str(session_id),
                        chunk="",
                        status="completed",
                        created_at=time.time(),
                        model="tongyi",
                        is_final=True
                    )
                    yield f"data: {final_response.model_dump_json()}\n\n"

            except Exception as e:
                # 如果流处理过程中出现错误，发送错误信息
                logger.error(f"流式处理过程中出现错误: {str(e)}")
                error_response = ChunkChatCompletionResponse(
                    session_id=str(session_id),
                    chunk=f"处理过程中出现错误: {str(e)}",
                    status="error",
                    created_at=time.time(),
                    model="tongyi",
                    is_final=True
                )
                yield f"data: {error_response.model_dump_json()}\n\n"

            finally:
                # 确保发送流结束标记
                yield "data: [DONE]\n\n"

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
