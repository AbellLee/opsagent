from typing import Annotated, Sequence, TypedDict, List, Any
from langgraph.graph import MessagesState
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """Agent状态定义"""
    # Messages具有自动处理消息追加的特殊行为
    messages: Annotated[Sequence[BaseMessage], MessagesState]
    
    # 用户ID，用于个性化工具审批配置
    user_id: str
    
    # 会话ID，用于持久化检查点
    session_id: str
    
    # 当前工具执行是否需要审批
    tool_approval_required: bool
    
    # 待审批的工具信息
    pending_tool_approvals: List[Any]
    
    # Agent执行的中间状态
    intermediate_steps: List[Any]

# 可以根据需要添加更多状态字段