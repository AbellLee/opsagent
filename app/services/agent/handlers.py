"""
Agent服务的核心业务逻辑处理
"""
from typing import Dict, Any, Optional, List
from uuid import UUID
import time
import uuid
from datetime import datetime
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import BaseTool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres.aio import AsyncPostgresStore

from app.core.logger import get_logger
from app.core.config import settings
from app.agent.graph import create_graph_async
from app.models.schemas import ChatCompletionResponse, ChunkChatCompletionResponse
from app.services.agent.utils import build_agent_inputs, create_agent_config

# 使用模块级logger
logger = get_logger("services.agent.handlers")


async def execute_agent_task(
    session_id: UUID,
    message: str,
    tools: Optional[List[BaseTool]] = None,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """执行Agent任务的核心业务逻辑

    Args:
        session_id: 会话ID
        message: 用户消息内容
        tools: 可用工具列表，默认为None（使用默认工具）
        config: Agent配置字典，默认为None（使用默认配置）

    Returns:
        包含以下字段的字典：
        - session_id: 会话ID
        - response: AI响应内容
        - status: 执行状态 ("success" | "error")

    Example:
        >>> result = await execute_agent_task(
        ...     session_id=UUID("..."),
        ...     message="Hello, how are you?"
        ... )
        >>> print(result["response"])
    """
    # 构造输入
    inputs = build_agent_inputs(message, session_id)

    # 使用异步上下文管理器
    async with AsyncPostgresSaver.from_conn_string(settings.database_url) as checkpointer:
        # 确保检查点表已创建
        await checkpointer.setup()
        # 创建新的agent graph实例（异步加载MCP工具）
        agent_graph = await create_graph_async(checkpointer=checkpointer)
        # 执行Agent图，并传入检查点配置
        config = create_agent_config(session_id)
        result = await agent_graph.ainvoke(inputs, config)
    
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


async def handle_blocking_chat(
    session_id: UUID,
    inputs: Dict[str, Any],
    config: Dict[str, Any]
) -> ChatCompletionResponse:
    """处理阻塞模式的聊天 - 使用LangGraph标准流程

    Args:
        session_id: 会话ID
        inputs: Agent输入数据，包含messages等字段
        config: LangGraph配置对象，包含thread_id等

    Returns:
        ChatCompletionResponse对象，包含完整的响应信息

    Raises:
        Exception: 当Agent执行失败时
    """
    # 使用异步上下文管理器
    async with (
        AsyncPostgresStore.from_conn_string(settings.database_url) as store,
        AsyncPostgresSaver.from_conn_string(settings.database_url) as checkpointer,
    ):
        # 确保检查点表已创建
        await checkpointer.setup()

        # 创建graph实例（异步加载MCP工具）
        graph = await create_graph_async(checkpointer=checkpointer, store=store)

        # 执行graph（异步）
        result = await graph.ainvoke(inputs, config)

        # 获取执行过程中的所有新消息
        messages = result.get("messages", [])

        # 导入消息合并函数
        from app.api.routes.sessions import merge_tool_messages

        # 合并工具相关消息
        merged_messages = merge_tool_messages(messages)

        # 获取最后的AI助手消息作为response
        response_message = None
        for message in reversed(merged_messages):
            if message.get("type") == "assistant":
                response_message = message
                break

        if not response_message:
            # 如果没有找到AI消息，创建一个默认的
            response_message = {
                "id": str(uuid.uuid4()),
                "type": "assistant",
                "role": "assistant",
                "content": "抱歉，没有收到回复。",
                "timestamp": datetime.now().isoformat(),
                "sender": "AI助手"
            }

        # 将消息内容转换为字符串格式
        if isinstance(response_message, dict):
            # 如果是字典，提取content字段或转换为JSON字符串
            response_content = response_message.get("content", "")
            if isinstance(response_content, list):
                # 如果content是列表，提取其中的文本内容
                text_contents = [item.get("content", "") for item in response_content if item.get("type") == "text"]
                response_content = "\n".join(text_contents)
            elif not isinstance(response_content, str):
                # 如果content不是字符串，转换为JSON字符串
                import json
                response_content = json.dumps(response_content, ensure_ascii=False)
        else:
            # 如果不是字典，直接转换为字符串
            response_content = str(response_message)

        return ChatCompletionResponse(
            session_id=str(session_id),
            response=response_content,  # 返回字符串格式的响应
            status="success",
            created_at=time.time(),
            model="tongyi"
        )


async def handle_streaming_chat(session_id: UUID, inputs: Dict[str, Any], config: Dict[str, Any]):
    """处理流式模式的聊天 - 使用LangGraph标准流程进行流式输出"""

    async def generate_stream():
        """生成SSE流式数据（异步生成器）"""

        async with (
            AsyncPostgresStore.from_conn_string(settings.database_url) as store,
            AsyncPostgresSaver.from_conn_string(settings.database_url) as checkpointer,
        ):

            # 创建graph实例（异步加载MCP工具）
            graph = await create_graph_async(checkpointer=checkpointer, store=store)

            # 回到messages模式，但改进工具调用处理逻辑
            # 重要：不要中途break，让LangGraph完整执行以确保状态正确保存
            try:
                stream_finished = False
                pending_tool_calls = {}  # 存储待完成的工具调用
                message_count = 0

                async for chunk, _ in graph.astream(inputs, config, stream_mode="messages"):
                    message_count += 1

                    # 处理AIMessage - 包括普通回复和工具调用
                    if isinstance(chunk, AIMessage):
                        # 检查是否包含工具调用
                        tool_calls = getattr(chunk, 'tool_calls', [])
                        ai_content = getattr(chunk, 'content', '')

                        # 先发送AI的文本内容（如果有）
                        if ai_content and ai_content.strip():
                            chunk_response = ChunkChatCompletionResponse(
                                session_id=str(session_id),
                                chunk=ai_content,
                                status="streaming",
                                created_at=time.time(),
                                model="tongyi",
                                is_final=False,
                                message_type="assistant"
                            )
                            yield f"data: {chunk_response.model_dump_json()}\n\n"

                        # 如果有工具调用，立即发送工具调用信息（不等待结果）
                        if tool_calls:
                            for tool_call in tool_calls:
                                # 尝试多种方式获取工具调用信息
                                tool_name = ''
                                tool_id = ''
                                tool_args = {}

                                # 方式1：直接属性访问
                                if hasattr(tool_call, 'name'):
                                    tool_name = getattr(tool_call, 'name', '') or ''
                                if hasattr(tool_call, 'id'):
                                    tool_id = getattr(tool_call, 'id', '') or ''
                                if hasattr(tool_call, 'args'):
                                    tool_args = getattr(tool_call, 'args', {}) or {}

                                # 方式2：字典访问（如果tool_call是字典）
                                if isinstance(tool_call, dict):
                                    tool_name = tool_call.get('name', '') or tool_name
                                    tool_id = tool_call.get('id', '') or tool_id
                                    tool_args = tool_call.get('args', {}) or tool_args

                                # 方式3：检查function属性（某些LLM返回格式）
                                if hasattr(tool_call, 'function'):
                                    func = getattr(tool_call, 'function', {})
                                    if hasattr(func, 'name'):
                                        tool_name = getattr(func, 'name', '') or tool_name
                                    if hasattr(func, 'arguments'):
                                        import json
                                        try:
                                            tool_args = json.loads(getattr(func, 'arguments', '{}')) or tool_args
                                        except:
                                            pass

                                if tool_name.strip() and tool_id.strip():
                                    # 立即发送工具调用信息（状态为calling）
                                    tool_call_info = {
                                        "id": tool_id,
                                        "name": tool_name,
                                        "args": tool_args,
                                        "type": "tool_call",
                                        "result": None,
                                        "status": "calling"
                                    }

                                    chunk_response = ChunkChatCompletionResponse(
                                        session_id=str(session_id),
                                        chunk="",
                                        status="streaming",
                                        created_at=time.time(),
                                        model="tongyi",
                                        is_final=False,
                                        message_type="tool_call",
                                        tool_calls=[tool_call_info]
                                    )
                                    yield f"data: {chunk_response.model_dump_json()}\n\n"

                                    # 存储工具调用，等待结果更新
                                    pending_tool_calls[tool_id] = tool_call_info

                    # 处理ToolMessage - 工具执行结果
                    elif isinstance(chunk, ToolMessage):
                        tool_call_id = getattr(chunk, 'tool_call_id', '')
                        tool_result = getattr(chunk, 'content', '')

                        # 如果找到对应的工具调用，发送更新后的工具调用信息
                        if tool_call_id in pending_tool_calls:
                            tool_call_info = pending_tool_calls[tool_call_id]
                            tool_call_info["result"] = tool_result
                            tool_call_info["status"] = "completed"

                            # 发送更新后的工具调用信息
                            chunk_response = ChunkChatCompletionResponse(
                                session_id=str(session_id),
                                chunk="",
                                status="streaming",
                                created_at=time.time(),
                                model="tongyi",
                                is_final=False,
                                message_type="tool_result",
                                tool_call_id=tool_call_id,
                                tool_name=tool_call_info["name"],
                                tool_calls=None
                            )
                            chunk_response.chunk = tool_result  # 设置结果内容
                            yield f"data: {chunk_response.model_dump_json()}\n\n"

                            # 移除已完成的工具调用
                            del pending_tool_calls[tool_call_id]

                logger.info(f"消息处理完成，总共处理了 {message_count} 条消息")

                # 图执行完毕后，如果还没有发送结束信号，则发送
                if not stream_finished:
                    final_response = ChunkChatCompletionResponse(
                        session_id=str(session_id),
                        chunk="",
                        status="completed",
                        created_at=time.time(),
                        model="tongyi",
                        is_final=True,
                        message_type="assistant"
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
                    is_final=True,
                    message_type="assistant"
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
