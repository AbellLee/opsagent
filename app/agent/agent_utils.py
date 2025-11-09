"""Agent工具函数

包含LLM配置加载和消息修复等工具函数。
"""
from typing import List, Tuple
from langchain_core.messages import ToolMessage, AIMessage, BaseMessage
from langchain_core.runnables import RunnableConfig
from app.core.logger import get_logger
from app.core.llm import get_llm, LLMInitializationError

# 使用模块级logger
logger = get_logger("agent.utils")


def get_llm_from_config(config: RunnableConfig) -> Tuple:
    """从配置中获取LLM实例
    
    优先级：
    1. 如果配置中指定了model_config_id，使用数据库配置
    2. 否则使用默认的get_llm()（环境变量配置）
    
    Args:
        config: LangGraph配置对象，可包含以下configurable字段：
            - model_config_id: 数据库中的LLM配置ID (UUID字符串)
    
    Returns:
        tuple: (llm, embedding) 包含LLM和嵌入模型实例的元组
            - llm: 语言模型实例
            - embedding: 嵌入模型实例
    
    Raises:
        LLMInitializationError: 当LLM初始化失败时
    
    Example:
        >>> config = {"configurable": {"model_config_id": "uuid-string"}}
        >>> llm, embedding = get_llm_from_config(config)
        >>> response = llm.invoke("Hello")
    
    Note:
        如果数据库配置加载失败，会自动回退到环境变量配置
    """
    model_config_id = config.get("configurable", {}).get("model_config_id")
    
    if model_config_id:
        # 使用数据库配置
        try:
            from app.core.llm_manager import LLMManager
            from app.db.session import get_db_sqlalchemy
            from uuid import UUID
            
            # 获取数据库会话
            db = next(get_db_sqlalchemy())
            try:
                llm_manager = LLMManager(db)
                config_id = UUID(model_config_id)
                llm, embedding = llm_manager.get_llm_and_embedding(chat_config_id=config_id)
                logger.info(f"使用数据库LLM配置: {model_config_id}")
                return llm, embedding
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"使用数据库配置失败: {e}，回退到默认配置", exc_info=True)
            # 回退到默认配置
            return get_llm()
    else:
        # 使用默认配置（环境变量）
        return get_llm()


def fix_incomplete_tool_calls(messages: List[BaseMessage]) -> List[BaseMessage]:
    """修复不完整的消息序列，确保所有包含tool_calls的AIMessage都有对应的ToolMessage
    
    当从检查点恢复对话时，可能存在包含tool_calls但没有对应ToolMessage的AIMessage，
    这会导致API错误。此函数会检测这种情况并添加占位的ToolMessage。
    
    Args:
        messages: 原始消息列表
    
    Returns:
        修复后的消息列表，所有tool_calls都有对应的ToolMessage
    
    Example:
        >>> messages = [
        ...     AIMessage(content="", tool_calls=[{"id": "1", "name": "search"}]),
        ...     # 缺少ToolMessage
        ... ]
        >>> fixed = fix_incomplete_tool_calls(messages)
        >>> # 会自动添加占位的ToolMessage
    """
    fixed_messages = []
    tool_call_ids = set()  # 跟踪已有的tool_call_id
    processed_tool_calls = set()  # 跟踪已处理的tool_call_id
    
    # 第一遍：收集所有已有的ToolMessage的tool_call_id
    for msg in messages:
        if isinstance(msg, ToolMessage) and hasattr(msg, 'tool_call_id'):
            tool_call_ids.add(msg.tool_call_id)
    
    # 第二遍：处理消息，修复不完整的tool_calls
    for msg in messages:
        fixed_messages.append(msg)
        
        # 检查AIMessage是否有未完成的tool_calls
        if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tool_call in msg.tool_calls:
                # 获取tool_call_id，支持不同的格式
                tool_call_id = None
                if isinstance(tool_call, dict):
                    tool_call_id = tool_call.get('id')
                elif hasattr(tool_call, 'id'):
                    tool_call_id = tool_call.id
                
                # 如果tool_call_id存在且没有对应的ToolMessage，则添加占位符
                if tool_call_id and tool_call_id not in tool_call_ids and tool_call_id not in processed_tool_calls:
                    # 添加占位的ToolMessage
                    placeholder_msg = ToolMessage(
                        content="工具调用被中断或未完成",
                        tool_call_id=tool_call_id
                    )
                    fixed_messages.append(placeholder_msg)
                    processed_tool_calls.add(tool_call_id)
                    logger.info(f"添加了占位ToolMessage用于未完成的tool_call_id: {tool_call_id}")
    
    # 如果对消息进行了修复，记录日志
    if len(fixed_messages) != len(messages):
        logger.info(f"修复了不完整的消息序列: 原始{len(messages)}条消息 -> 修复后{len(fixed_messages)}条消息")
    
    return fixed_messages

