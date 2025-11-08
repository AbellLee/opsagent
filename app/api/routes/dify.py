"""
Dify API 兼容路由
提供与 Dify API 兼容的接口
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from app.models.schemas import DifyChatRequest, DifyChatResponse, DifyStreamResponse
from app.api.deps import get_db
from app.core.logger import logger
from uuid import uuid4, UUID
from datetime import datetime
import json
import time
from typing import AsyncGenerator, Optional

router = APIRouter(prefix="/v1", tags=["Dify Compatible API"])


async def stream_dify_response(
    session_id: str,
    message: str,
    user_id: str,
    db,
    model_config_id: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """
    生成Dify格式的流式响应

    Args:
        session_id: 会话ID
        message: 用户消息
        user_id: 用户ID
        db: 数据库连接
        model_config_id: LLM配置ID（可选）
    """
    from app.services.agent.handlers import handle_streaming_chat
    from app.services.agent.utils import build_agent_inputs, create_agent_config
    from uuid import UUID

    # 构建输入和配置
    session_uuid = UUID(session_id)
    inputs = build_agent_inputs(message, session_uuid, user_id)
    config = create_agent_config(session_uuid)

    # 如果指定了模型配置，添加到配置中
    if model_config_id:
        config["configurable"]["model_config_id"] = model_config_id

    message_id = str(uuid4())
    conversation_id = session_id
    created_at = int(time.time())

    # 发送开始事件
    start_event = {
        "event": "message",
        "message_id": message_id,
        "conversation_id": conversation_id,
        "created_at": created_at
    }
    yield f"data: {json.dumps(start_event)}\n\n"

    # 处理流式聊天
    full_answer = ""
    stream_response = await handle_streaming_chat(session_uuid, inputs, config)

    # handle_streaming_chat 返回 StreamingResponse，我们需要从中提取数据
    # 由于它返回的是 StreamingResponse，我们需要直接调用底层的生成器
    # 让我们重新实现这部分逻辑
    from app.services.agent.handlers import handle_streaming_chat
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    from langgraph.store.postgres import AsyncPostgresStore
    from app.core.config import settings
    from app.agent.graph import create_graph_async

    async with (
        AsyncPostgresStore.from_conn_string(settings.database_url) as store,
        AsyncPostgresSaver.from_conn_string(settings.database_url) as checkpointer,
    ):
        await checkpointer.setup()
        graph = await create_graph_async(checkpointer=checkpointer, store=store)

        # 流式执行graph
        async for event in graph.astream(inputs, config, stream_mode="messages"):
            # 处理不同类型的事件
            if isinstance(event, tuple) and len(event) == 2:
                message_obj, metadata = event

                # 检查消息类型
                if hasattr(message_obj, 'type'):
                    msg_type = message_obj.type

                    if msg_type == 'ai':
                        # AI消息
                        content = getattr(message_obj, 'content', '')
                        if content:
                            full_answer += content
                            dify_chunk = {
                                "event": "agent_message",
                                "message_id": message_id,
                                "conversation_id": conversation_id,
                                "answer": content,
                                "created_at": created_at
                            }
                            yield f"data: {json.dumps(dify_chunk, ensure_ascii=False)}\n\n"

                    elif msg_type == 'tool':
                        # 工具调用
                        tool_name = getattr(message_obj, 'name', 'unknown')
                        thought_event = {
                            "event": "agent_thought",
                            "message_id": message_id,
                            "conversation_id": conversation_id,
                            "thought": f"调用工具: {tool_name}",
                            "tool": tool_name,
                            "created_at": created_at
                        }
                        yield f"data: {json.dumps(thought_event, ensure_ascii=False)}\n\n"

    # 发送结束事件
    end_event = {
        "event": "message_end",
        "message_id": message_id,
        "conversation_id": conversation_id,
        "metadata": {
            "usage": {
                "total_tokens": 0
            }
        },
        "created_at": created_at
    }
    yield f"data: {json.dumps(end_event)}\n\n"


@router.post("/chat-messages", response_model=DifyChatResponse)
async def chat_messages(
    request: DifyChatRequest,
    db = Depends(get_db)
):
    """
    Dify兼容的聊天消息接口
    支持阻塞和流式两种响应模式
    """
    try:
        # 处理conversation_id
        if request.conversation_id:
            # 使用现有会话
            try:
                session_id = str(UUID(request.conversation_id))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="无效的conversation_id格式"
                )
            
            # 验证会话是否存在
            cursor = db.cursor()
            cursor.execute(
                "SELECT session_id FROM user_sessions WHERE session_id = %s",
                (session_id,)
            )
            if not cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="会话不存在"
                )
        else:
            # 创建新会话
            from datetime import timedelta

            session_id = str(uuid4())
            created_at = datetime.now()
            expires_at = created_at + timedelta(hours=24)

            # 查找或创建用户
            cursor = db.cursor()
            cursor.execute(
                "SELECT user_id FROM users WHERE username = %s",
                (request.user,)
            )
            user_row = cursor.fetchone()

            if user_row:
                user_id = str(user_row[0])
            else:
                # 创建新用户
                user_id = str(uuid4())
                cursor.execute(
                    """
                    INSERT INTO users (user_id, username, email, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (user_id, request.user, f"{request.user}@dify.local", created_at, created_at)
                )

            # 验证 LLM 配置（如果提供）
            llm_config_id = None
            if request.model_config_id:
                try:
                    llm_config_id = str(UUID(request.model_config_id))
                    # 验证配置是否存在且激活
                    cursor.execute(
                        "SELECT id FROM llm_configs WHERE id = %s AND is_active = true",
                        (llm_config_id,)
                    )
                    if not cursor.fetchone():
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="指定的LLM配置不存在或未激活"
                        )
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="无效的model_config_id格式"
                    )

            # 创建会话（包含 LLM 配置关联）
            cursor.execute(
                """
                INSERT INTO user_sessions (session_id, user_id, session_name, llm_config_id, created_at, expires_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (session_id, user_id, "Dify Chat", llm_config_id, created_at, expires_at)
            )
            db.commit()
        
        # 根据响应模式处理请求
        if request.response_mode == "streaming":
            # 流式响应
            return StreamingResponse(
                stream_dify_response(
                    session_id,
                    request.query,
                    user_id,
                    db,
                    model_config_id=request.model_config_id
                ),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        else:
            # 阻塞响应
            from app.services.agent.handlers import handle_blocking_chat
            from app.services.agent.utils import build_agent_inputs, create_agent_config
            from uuid import UUID

            session_uuid = UUID(session_id)
            inputs = build_agent_inputs(request.query, session_uuid, user_id)
            config = create_agent_config(session_uuid)

            # 如果指定了模型配置，添加到配置中
            if request.model_config_id:
                config["configurable"]["model_config_id"] = request.model_config_id

            response = await handle_blocking_chat(session_uuid, inputs, config)
            
            message_id = str(uuid4())
            created_at = int(time.time())
            
            return DifyChatResponse(
                event="message",
                message_id=message_id,
                conversation_id=session_id,
                mode="chat",
                answer=response.response,
                metadata={
                    "usage": response.usage or {}
                },
                created_at=created_at
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dify chat-messages API错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理请求失败: {str(e)}"
        )


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    db = Depends(get_db)
):
    """
    获取会话信息
    """
    try:
        session_id = str(UUID(conversation_id))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的conversation_id格式"
        )
    
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT session_id, user_id, session_name, created_at
        FROM user_sessions
        WHERE session_id = %s
        """,
        (session_id,)
    )
    row = cursor.fetchone()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    return {
        "id": str(row[0]),
        "name": row[2],
        "created_at": int(row[3].timestamp()) if row[3] else None
    }


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db = Depends(get_db)
):
    """
    删除会话
    """
    try:
        session_id = str(UUID(conversation_id))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的conversation_id格式"
        )
    
    cursor = db.cursor()
    cursor.execute(
        "DELETE FROM user_sessions WHERE session_id = %s",
        (session_id,)
    )
    
    if cursor.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    db.commit()
    
    return {"result": "success"}

