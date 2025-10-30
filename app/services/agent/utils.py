"""
Agent服务相关的工具函数
"""
from typing import List, Dict, Any
from uuid import UUID, uuid4
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from app.core.logger import logger


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


def build_agent_inputs(message: str, session_id: UUID, user_id: str = None) -> Dict[str, Any]:
    """构造Agent输入数据"""
    # 如果没有提供user_id，则生成一个临时的UUID
    if user_id is None:
        user_id = str(uuid4())
        
    return {
        "messages": [
            HumanMessage(content=message.strip())
        ],
        "user_id": user_id,
        "session_id": str(session_id),
        "tool_approval_required": False,
        "pending_tool_approvals": [],
        "intermediate_steps": []
    }


def create_agent_config(session_id: UUID) -> Dict[str, Any]:
    """创建Agent配置"""
    return {
        "configurable": {
            "thread_id": str(session_id)
        }
    }


def format_error_message(error: Exception) -> str:
    """格式化错误消息，提供更友好的错误提示"""
    error_detail = str(error)
    
    # 检查是否是数据库连接错误
    if "数据库连接失败" in error_detail or "connection to server" in error_detail:
        return "数据库连接失败，请检查数据库服务是否运行正常"
    
    # 如果是模型API密钥问题，提供更明确的错误信息
    elif "api key" in error_detail.lower() or "dashscope" in error_detail.lower():
        return "模型服务未配置：请配置通义千问API密钥(DASHSCOPE_API_KEY)才能使用AI功能"
    
    return error_detail