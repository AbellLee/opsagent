"""
Agent服务相关的工具函数
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage, BaseMessage
from app.core.logger import get_logger

# 使用模块级logger
logger = get_logger("services.agent.utils")


def get_session_messages_from_db(db, session_id: UUID) -> List[BaseMessage]:
    """从数据库获取会话历史消息

    Args:
        db: 数据库连接对象
        session_id: 会话ID

    Returns:
        消息列表，按时间升序排列

    Example:
        >>> messages = get_session_messages_from_db(db, session_id)
        >>> print(f"加载了 {len(messages)} 条消息")

    Note:
        如果查询失败，返回空列表
    """
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
        logger.error(f"获取会话历史消息失败: {e}", exc_info=True)
        return []


def build_agent_inputs(message: str, session_id: UUID, user_id: str = "default_user", files: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """构造Agent输入数据,支持多模态内容(文本+图片)

    Args:
        message: 文本消息内容
        session_id: 会话ID
        user_id: 用户ID
        files: 文件列表,每个文件包含 type 和 url/data 字段
               例如: [{"type": "image", "url": "https://..."}, {"type": "image", "data": "base64..."}]

    Returns:
        包含消息和配置的字典
    """
    # 构建消息内容
    if files and len(files) > 0:
        # 多模态消息: 文本 + 图片
        content = []

        # 添加文本内容
        if message and message.strip():
            content.append({
                "type": "text",
                "text": message.strip()
            })

        # 添加图片内容
        for file in files:
            if file.get("type") == "image":
                # 支持 URL 或 base64 数据
                if "url" in file:
                    content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": file["url"]
                        }
                    })
                elif "data" in file:
                    # base64 格式: data:image/jpeg;base64,/9j/4AAQ...
                    content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": file["data"]
                        }
                    })

        human_message = HumanMessage(content=content)
    else:
        # 纯文本消息
        human_message = HumanMessage(content=message.strip())

    return {
        "messages": [human_message],
        "user_id": user_id,
        "session_id": str(session_id),
        "tool_approval_required": False,
        "pending_tool_approvals": [],
        "intermediate_steps": []
    }


def create_agent_config(session_id: UUID) -> Dict[str, Any]:
    """创建Agent配置

    Args:
        session_id: 会话ID

    Returns:
        LangGraph配置字典，包含thread_id用于检查点管理

    Example:
        >>> config = create_agent_config(session_id)
        >>> result = await graph.ainvoke(inputs, config)
    """
    return {
        "configurable": {
            "thread_id": str(session_id)
        }
    }


def format_error_message(error: Exception) -> str:
    """格式化错误消息，提供更友好的错误提示

    Args:
        error: 异常对象

    Returns:
        格式化后的错误消息字符串

    Example:
        >>> try:
        ...     # some operation
        ... except Exception as e:
        ...     friendly_msg = format_error_message(e)
        ...     print(friendly_msg)
    """
    error_detail = str(error)

    # 检查是否是数据库连接错误
    if "数据库连接失败" in error_detail or "connection to server" in error_detail:
        return "数据库连接失败，请检查数据库服务是否运行正常"

    # 如果是模型API密钥问题，提供更明确的错误信息
    elif "api key" in error_detail.lower() or "dashscope" in error_detail.lower():
        return "模型服务未配置：请配置通义千问API密钥(DASHSCOPE_API_KEY)才能使用AI功能"

    return error_detail