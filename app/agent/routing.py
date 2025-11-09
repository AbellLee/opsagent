"""Agent路由函数

包含决定Agent执行流程的路由逻辑。
"""
from app.core.logger import get_logger
from app.agent.state import AgentState

# 使用模块级logger
logger = get_logger("agent.routing")


def should_continue(state: AgentState) -> str:
    """决定是否继续执行工具
    
    Args:
        state: Agent状态，包含消息历史
    
    Returns:
        "tools" 如果需要执行工具，"end" 如果对话结束
    
    Example:
        >>> from langchain_core.messages import AIMessage
        >>> state = {"messages": [AIMessage(content="", tool_calls=[...])]}
        >>> result = should_continue(state)
        >>> print(result)  # "tools"
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        tool_names = [tc['name'] for tc in last_message.tool_calls]
        logger.info(f"检测到工具调用: {tool_names}")
        return "tools"
    
    logger.info("没有工具调用，结束对话")
    return "end"

