from typing import Dict, Any
from langchain_core.messages import ToolMessage, AIMessage
from langgraph.graph import StateGraph, END, MessagesState
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore
from app.agent.model import qwen_model
from app.agent.tools import tool_manager
from app.core.config import settings
from app.core.logger import logger
import os

# 定义节点函数
def call_model(state: MessagesState) -> Dict[str, Any]:
    """调用模型"""
    try:
        # 使用qwen_model.generate_response方法生成响应
        messages = [{"role": msg.type, "content": msg.content} for msg in state["messages"]]
        response_content = qwen_model.generate_response(messages)
        response = AIMessage(content=response_content)
        return {"messages": [response]}
    except Exception as e:
        logger.error(f"调用模型失败: {e}")
        return {"messages": [AIMessage(content=f"模型调用失败: {str(e)}")]}

def should_continue(state: MessagesState) -> str:
    """决定是否继续执行工具"""
    messages = state["messages"]
    last_message = messages[-1] if messages else None
    
    # 这里可以实现更复杂的逻辑来决定是否需要执行工具
    # 目前简化处理，假设模型会明确指示是否需要工具
    if last_message and hasattr(last_message, 'content'):
        content = last_message.content
        # 简单示例：如果模型响应中包含"tool:"则执行工具
        if "tool:" in content.lower():
            return "tools"
    
    return "end"

def route_tools(state: MessagesState) -> Dict[str, Any]:
    """路由到工具执行"""
    messages = state["messages"]
    last_message = messages[-1] if messages else None
    
    if not last_message or not hasattr(last_message, 'content'):
        return {"messages": []}
    
    content = last_message.content
    
    # 简单示例：从模型响应中提取工具名称和参数
    # 在实际应用中，应该使用更复杂的解析逻辑或结构化输出
    if "tool:" in content.lower():
        # 提取工具名称和参数（简化处理）
        try:
            tool_part = content.split("tool:", 1)[1].strip()
            tool_name = tool_part.split()[0] if tool_part.split() else ""
            
            # 执行工具（可能需要审批）
            tool_result = tool_manager.execute_tool(tool_name, {})
            
            # 检查是否需要审批
            if tool_result.get("status") == "pending_approval":
                # 返回提示信息
                return {"messages": [AIMessage(content=f"工具 {tool_name} 需要审批后才能执行")]}
            
            # 直接执行工具并将结果作为消息添加到状态中
            tool_message = ToolMessage(
                content=str(tool_result),
                tool_call_id=tool_name
            )
            
            return {"messages": [tool_message]}
        except Exception as e:
            logger.error(f"工具执行路由失败: {e}")
            return {"messages": [AIMessage(content=f"工具执行失败: {str(e)}")]}
    
    return {"messages": []}

# 构建图
def create_agent_graph():
    """创建Agent图"""

    with (
        PostgresStore.from_conn_string(settings.database_url) as store,
        PostgresSaver.from_conn_string(settings.database_url) as checkpointer,
    ):
        builder  = StateGraph(MessagesState)

        # 添加节点
        builder.add_node("agent", call_model)
        builder.add_node("tools", route_tools)
        
        # 设置入口点
        builder.set_entry_point("agent")
        
        # 添加条件边，根据should_continue函数的返回值决定下一步
        builder.add_conditional_edges(
            "agent",
            should_continue,
            {
                "tools": "tools",
                "end": END
            }
        )
        
        # 工具执行后返回agent节点继续处理
        builder.add_edge("tools", "agent")
        graph = builder.compile(
            checkpointer=checkpointer,
            store=store,
        )
    
    return graph
    
   

# 创建全局Agent图实例
agent_graph = create_agent_graph()