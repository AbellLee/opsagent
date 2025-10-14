from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from app.models.schemas import Session, SessionCreate
from app.api.deps import get_db
from app.core.logger import logger

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

@router.post("", response_model=Session, status_code=status.HTTP_201_CREATED)
def create_session(session_create: SessionCreate, db = Depends(get_db)):
    """创建新会话"""
    try:
        session_id = uuid4()
        created_at = datetime.now()
        expires_at = created_at + timedelta(hours=24)  # 24小时后过期
        
        # 插入数据库
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO user_sessions (session_id, user_id, session_name, created_at, expires_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (str(session_id), str(session_create.user_id), "新建对话", created_at, expires_at)
        )
        db.commit()
        
        return Session(
            session_id=session_id,
            user_id=session_create.user_id,
            session_name="新建对话",
            created_at=created_at,
            expires_at=expires_at
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建会话失败: {str(e)}"
        )

@router.get("/{session_id}", response_model=Session)
def get_session(session_id: UUID, db = Depends(get_db)):
    """获取会话信息"""
    try:
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT session_id, user_id, session_name, created_at, expires_at
            FROM user_sessions
            WHERE session_id = %s
            """,
            (str(session_id),)
        )
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )
            
        return Session(
            session_id=UUID(row[0]),
            user_id=UUID(row[1]),
            session_name=row[2],
            created_at=row[3],
            expires_at=row[4]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取会话信息失败: {str(e)}"
        )

@router.put("/{session_id}/name")
def update_session_name(session_id: UUID, session_name: str, db = Depends(get_db)):
    """更新会话名称"""
    try:
        cursor = db.cursor()
        cursor.execute(
            """
            UPDATE user_sessions 
            SET session_name = %s 
            WHERE session_id = %s
            """,
            (session_name, str(session_id))
        )
        db.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )
            
        return {"message": "会话名称更新成功"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新会话名称失败: {str(e)}"
        )

@router.delete("/{session_id}")
def delete_session(session_id: UUID, db = Depends(get_db)):
    """删除会话"""
    try:
        # 首先删除LangGraph检查点数据
        from langgraph.checkpoint.postgres import PostgresSaver
        from app.core.config import settings
        
        # 使用PostgresSaver删除检查点
        with PostgresSaver.from_conn_string(settings.database_url) as checkpointer:
            checkpointer.delete_thread(str(session_id))
        
        # 然后删除用户会话表中的数据
        cursor = db.cursor()
        cursor.execute(
            "DELETE FROM user_sessions WHERE session_id = %s",
            (str(session_id),)
        )
        db.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )
            
        return {"message": "会话删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除会话失败: {str(e)}"
        )

@router.get("/", response_model=List[Session])
def list_sessions(user_id: UUID = Query(...), db = Depends(get_db)):
    """列出用户的所有会话"""
    try:
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT session_id, user_id, session_name, created_at, expires_at
            FROM user_sessions
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (str(user_id),)
        )
        rows = cursor.fetchall()
        
        sessions = []
        for row in rows:
            sessions.append(Session(
                session_id=UUID(row[0]),
                user_id=UUID(row[1]),
                session_name=row[2],
                created_at=row[3],
                expires_at=row[4]
            ))
            
        return sessions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取会话列表失败: {str(e)}"
        )


def format_message_for_frontend(msg):
    """将LangChain消息格式化为前端需要的格式"""
    import uuid
    from app.core.logger import logger

    base_message = {
        "id": getattr(msg, 'id', str(uuid.uuid4())),
        "timestamp": getattr(msg, 'timestamp', datetime.now().isoformat()) if hasattr(msg, 'timestamp') else datetime.now().isoformat()
    }

    logger.debug(f"格式化消息: type={getattr(msg, 'type', 'unknown')}, content={getattr(msg, 'content', '')[:50]}...")

    if hasattr(msg, 'type'):
        if msg.type == "human":
            return {
                **base_message,
                "type": "user",
                "role": "user",
                "content": getattr(msg, 'content', ''),
                "sender": "用户"
            }
        elif msg.type == "ai":
            # 检查是否包含工具调用
            tool_calls = getattr(msg, 'tool_calls', [])
            if tool_calls:
                return {
                    **base_message,
                    "type": "tool_call",
                    "role": "assistant",
                    "content": getattr(msg, 'content', ''),
                    "tool_calls": tool_calls,
                    "sender": "AI助手"
                }
            else:
                return {
                    **base_message,
                    "type": "assistant",
                    "role": "assistant",
                    "content": getattr(msg, 'content', ''),
                    "sender": "AI助手"
                }
        elif msg.type == "tool":
            return {
                **base_message,
                "type": "tool_result",
                "role": "tool",
                "content": getattr(msg, 'content', ''),
                "tool_name": getattr(msg, 'name', ''),
                "tool_call_id": getattr(msg, 'tool_call_id', ''),
                "sender": f"工具: {getattr(msg, 'name', '未知工具')}"
            }

    # 过滤掉不支持的消息类型
    return None


def merge_tool_messages(messages):
    """合并工具调用和工具结果消息"""
    import uuid
    from app.core.logger import logger

    logger.info(f"开始合并工具消息，原始消息数量: {len(messages)}")

    formatted_messages = []
    i = 0

    while i < len(messages):
        msg = messages[i]
        formatted_msg = format_message_for_frontend(msg)

        if not formatted_msg:
            i += 1
            continue

        logger.info(f"处理消息 {i}: type={formatted_msg.get('type')}, content={formatted_msg.get('content', '')[:50]}...")

        # 如果是工具调用消息，查找后续的工具结果消息
        if formatted_msg.get("type") == "tool_call":
            logger.info(f"发现工具调用消息，开始合并")
            tool_operation_msg = {
                "id": str(uuid.uuid4()),
                "type": "tool_operation",
                "role": "assistant",
                "content": formatted_msg.get("content", ""),
                "tool_calls": formatted_msg.get("tool_calls", []),
                "tool_results": [],
                "current_step": "calling",
                "timestamp": formatted_msg.get("timestamp"),
                "sender": "AI助手"
            }

            # 查找后续的工具结果消息
            j = i + 1
            tool_results_found = 0
            while j < len(messages):
                next_msg = messages[j]
                next_formatted = format_message_for_frontend(next_msg)

                if not next_formatted:
                    j += 1
                    continue

                if next_formatted.get("type") == "tool_result":
                    # 将工具结果添加到工具操作消息中
                    tool_operation_msg["tool_results"].append({
                        "tool_name": next_formatted.get("tool_name", ""),
                        "tool_call_id": next_formatted.get("tool_call_id", ""),
                        "content": next_formatted.get("content", "")
                    })
                    tool_operation_msg["current_step"] = "completed"
                    tool_results_found += 1
                    logger.info(f"找到工具结果消息 {tool_results_found}: {next_formatted.get('tool_name', '')}")
                    j += 1
                elif next_formatted.get("type") == "assistant" and tool_results_found > 0:
                    # 如果已经找到工具结果，且遇到AI回复，将其作为工具操作的回复内容
                    if next_formatted.get("content"):
                        tool_operation_msg["content"] = next_formatted.get("content", "")
                        logger.info(f"找到AI回复内容，添加到工具操作消息中")
                    j += 1
                    break
                else:
                    # 遇到其他类型消息，停止合并
                    logger.info(f"遇到其他类型消息: {next_formatted.get('type')}，停止合并")
                    break

            formatted_messages.append(tool_operation_msg)
            logger.info(f"工具操作消息合并完成，包含 {len(tool_operation_msg['tool_results'])} 个工具结果")
            i = j  # 跳过已处理的工具结果消息

        else:
            # 非工具调用消息，直接添加
            formatted_messages.append(formatted_msg)
            i += 1

    logger.info(f"消息合并完成，最终消息数量: {len(formatted_messages)}")
    return formatted_messages


@router.get("/{session_id}/messages")
def get_session_messages(session_id: UUID, db = Depends(get_db)):
    """获取会话历史消息，从LangGraph检查点加载"""
    try:
        from langgraph.checkpoint.postgres import PostgresSaver
        from app.core.config import settings
        from langchain_core.messages import HumanMessage, AIMessage
        
        # 使用PostgresSaver加载检查点数据
        with PostgresSaver.from_conn_string(settings.database_url) as checkpointer:
            # 构造检查点配置
            config = {
                "configurable": {
                    "thread_id": str(session_id)
                }
            }
            
            # 获取最后的检查点
            checkpoint = checkpointer.get(config)
            if not checkpoint:
                # 如果没有检查点，返回空消息列表
                return {"messages": []}
            
            # 从检查点中提取消息
            messages = []
            if "channel_values" in checkpoint and "messages" in checkpoint["channel_values"]:
                messages = checkpoint["channel_values"]["messages"]
            
            logger.info(f"从检查点加载了 {len(messages)} 条消息")

            # 使用新的格式化函数处理消息，并合并工具相关消息
            formatted_messages = merge_tool_messages(messages)

            logger.info(f"返回的消息类型统计: {[msg.get('type', 'unknown') for msg in formatted_messages]}")

            return {"messages": formatted_messages}
            
    except Exception as e:
        logger.error(f"获取会话消息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取会话消息失败: {str(e)}"
        )
