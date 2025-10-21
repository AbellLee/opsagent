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
            session_id=row[0] if isinstance(row[0], UUID) else UUID(row[0]),
            user_id=row[1] if isinstance(row[1], UUID) else UUID(row[1]),
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
        # 首先删除与该会话相关的所有任务
        cursor = db.cursor()
        cursor.execute(
            "DELETE FROM tasks WHERE session_id = %s",
            (str(session_id),)
        )
        task_count = cursor.rowcount
        db.commit()
        logger.info(f"已删除 {task_count} 个与会话 {session_id} 相关的任务")
        
        # 然后删除LangGraph检查点数据
        from langgraph.checkpoint.postgres import PostgresSaver
        from app.core.config import settings
        
        # 使用PostgresSaver删除检查点
        with PostgresSaver.from_conn_string(settings.database_url) as checkpointer:
            checkpointer.delete_thread(str(session_id))
        
        # 最后删除用户会话表中的数据
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
                session_id=row[0] if isinstance(row[0], UUID) else UUID(row[0]),
                user_id=row[1] if isinstance(row[1], UUID) else UUID(row[1]),
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
    logger.debug(f"format_message_for_frontend: {msg}")
    base_message = {
        "id": getattr(msg, 'id', str(uuid.uuid4())),
        "timestamp": getattr(msg, 'timestamp', datetime.now().isoformat()) if hasattr(msg, 'timestamp') else datetime.now().isoformat()
    }

    logger.info(f"格式化消息: id={base_message['id']}, type={getattr(msg, 'type', 'unknown')}, content={getattr(msg, 'content', '')[:50]}...")

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
            # AI消息统一返回assistant类型，工具调用信息保留在tool_calls字段中
            tool_calls = getattr(msg, 'tool_calls', [])
            return {
                **base_message,
                "type": "tool_call" if tool_calls else "assistant",
                "role": "assistant",
                "content": getattr(msg, 'content', ''),
                "tool_calls": tool_calls,
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
    """简化的消息处理 - Augment风格，按执行顺序交替构建序列"""
    import uuid
    from app.core.logger import logger

    logger.info(f"开始处理消息，原始消息数量: {len(messages)}")

    formatted_messages = []
    i = 0

    while i < len(messages):
        msg = messages[i]
        formatted_msg = format_message_for_frontend(msg)

        if not formatted_msg:
            i += 1
            continue

        # 如果是用户消息，直接添加
        if formatted_msg.get("type") == "user":
            formatted_messages.append(formatted_msg)
            i += 1
            continue

        # 如果是AI消息（包含工具调用或纯文本），开始构建AI消息序列
        if formatted_msg.get("type") == "assistant" or formatted_msg.get("type") == "tool_call":
            ai_message = {
                "id": str(uuid.uuid4()),
                "type": "assistant",
                "role": "assistant",
                "content": [],  # 按执行顺序的内容序列
                "timestamp": formatted_msg.get("timestamp"),
                "sender": "AI助手"
            }

            # 简单按顺序处理每个消息
            j = i
            while j < len(messages):
                current_msg = messages[j]
                current_formatted = format_message_for_frontend(current_msg)

                if not current_formatted:
                    j += 1
                    continue

                # 处理AI消息 - 按正确的执行顺序：先文本，后工具调用
                if current_formatted.get("type") == "tool_call" or current_formatted.get("type") == "assistant":
                    # 先添加文本内容（如果有）- 这是AI的分析或开始语句
                    ai_content = current_formatted.get("content", "")
                    if ai_content.strip():
                        text_entry = {
                            "type": "text",
                            "content": ai_content,
                            "status": "completed"
                        }
                        ai_message["content"].append(text_entry)


                    # 然后添加工具调用（如果有）- 这是AI要执行的操作
                    tool_calls = current_formatted.get("tool_calls", [])
                    for tool_call in tool_calls:
                        tool_call_entry = {
                            "type": "tool_call",
                            "id": tool_call.get("id", ""),
                            "name": tool_call.get("name", ""),
                            "args": tool_call.get("args", {}),
                            "result": None,
                            "status": "calling",
                            "expanded": False
                        }
                        ai_message["content"].append(tool_call_entry)

                    j += 1

                # 处理工具结果
                elif current_formatted.get("type") == "tool_result":
                    tool_call_id = current_formatted.get("tool_call_id", "")
                    tool_result = current_formatted.get("content", "")

                    # 查找对应的工具调用并更新结果
                    for content_item in ai_message["content"]:
                        if (content_item.get("type") == "tool_call" and
                            content_item.get("id") == tool_call_id):
                            content_item["status"] = "completed"
                            content_item["result"] = tool_result

                            break
                    j += 1

                else:
                    # 遇到其他类型消息，停止处理
                    break

            formatted_messages.append(ai_message)
            i = j

        else:
            # 其他类型消息，直接添加
            formatted_messages.append(formatted_msg)
            i += 1

    logger.info(f"消息处理完成，最终消息数量: {len(formatted_messages)}")
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

            # 详细日志：检查每个assistant消息的content结构
            for i, msg in enumerate(formatted_messages):
                if msg.get('type') == 'assistant':
                    content = msg.get('content', [])
                    if isinstance(content, list):
                        content_types = [item.get('type', 'unknown') for item in content]
                        logger.info(f"Assistant消息 {i}: content是数组，包含 {len(content)} 项，类型: {content_types}")
                    else:
                        logger.info(f"Assistant消息 {i}: content是字符串，长度: {len(str(content))}")

            return {"messages": formatted_messages}
            
    except Exception as e:
        logger.error(f"获取会话消息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取会话消息失败: {str(e)}"
        )


@router.get("/{session_id}/tasks")
def get_session_tasks(session_id: UUID, db = Depends(get_db)):
    """获取会话任务列表"""
    try:
        cursor = db.cursor()
        
        # 查询该会话下的所有任务
        cursor.execute("""
            SELECT id, user_id, session_id, content, status, parent_task_id, created_at, updated_at
            FROM tasks 
            WHERE session_id = %s
            ORDER BY created_at ASC
        """, (str(session_id),))
        
        tasks = cursor.fetchall()
        
        # 格式化任务数据
        formatted_tasks = []
        for task in tasks:
            formatted_tasks.append({
                "id": task[0],
                "user_id": str(task[1]) if task[1] else None,
                "session_id": str(task[2]) if task[2] else None,
                "content": task[3],
                "status": task[4],
                "parent_task_id": task[5],
                "created_at": task[6].isoformat() if task[6] else None,
                "updated_at": task[7].isoformat() if task[7] else None
            })
        
        return {"tasks": formatted_tasks}
        
    except Exception as e:
        logger.error(f"获取会话任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取会话任务失败: {str(e)}"
        )
