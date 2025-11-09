"""Agent图构建模块

包含创建和配置LangGraph图的函数。
"""
from typing import Any, Optional
from langgraph.graph import StateGraph, END
from langgraph.store.base import BaseStore
from langgraph.prebuilt import ToolNode

from app.core.logger import get_logger
from app.agent.state import AgentState
from app.agent.nodes import create_call_model_with_tools
from app.agent.routing import should_continue

# 使用模块级logger
logger = get_logger("agent.graph")


# ========================
# 构建图：create_graph
# ========================
async def create_graph_async(
    checkpointer: Optional[Any] = None,
    store: Optional[BaseStore] = None
):
    """创建Agent图（异步版本 - 支持MCP工具加载）

    Args:
        checkpointer: LangGraph检查点保存器，用于持久化对话状态
        store: 长期记忆存储，用于跨会话的记忆管理

    Returns:
        编译后的LangGraph图实例

    Example:
        >>> from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        >>> async with AsyncPostgresSaver.from_conn_string(db_url) as checkpointer:
        ...     graph = await create_graph_async(checkpointer=checkpointer)
        ...     result = await graph.ainvoke(inputs, config)
    """
    from app.agent.state import AgentState
    from app.agent.tools import tool_manager, mcp_manager

    builder = StateGraph(AgentState)

    # 获取自定义工具
    custom_tools = tool_manager.get_all_tools()
    logger.info(f"自定义工具数量: {len(custom_tools)}")

    # 异步加载MCP工具
    mcp_tools = await mcp_manager.get_mcp_tools()
    logger.info(f"MCP工具数量: {len(mcp_tools)}")

    # 合并所有工具
    available_tools = custom_tools + mcp_tools
    logger.info(f"总工具数量: {len(available_tools)}")

    # 创建带工具的call_model函数
    call_model_func = create_call_model_with_tools(available_tools)

    # 创建 ToolNode（如果工具存在）
    if available_tools:
        tool_node = ToolNode(available_tools)
        logger.info(f"创建 ToolNode，包含 {len(available_tools)} 个工具")
    else:
        tool_node = None
        logger.info("没有可用工具，不创建 ToolNode")

    # 添加节点
    builder.add_node("agent", call_model_func)  # 使用带工具的函数
    if tool_node:
        builder.add_node("tools", tool_node)

    # 设置入口
    builder.set_entry_point("agent")

    if tool_node:
        builder.add_conditional_edges(
            "agent",
            should_continue,
            {
                "tools": "tools",
                "end": END
            }
        )
        builder.add_edge("tools", "agent")
    else:
        builder.add_edge("agent", END)

    return builder.compile(checkpointer=checkpointer, store=store)


def create_graph(checkpointer=None, store=None):
    """创建 graph 图（同步版本 - 仅自定义工具，不包含MCP工具）"""
    from app.agent.state import AgentState
    from app.agent.tools import tool_manager

    builder = StateGraph(AgentState)

    # 只获取自定义工具
    available_tools = tool_manager.get_all_tools()
    logger.info(f"自定义工具数量: {len(available_tools)}")
    logger.warning("使用同步create_graph，MCP工具将不会被加载。请使用create_graph_async以支持MCP工具。")

    # 创建带工具的call_model函数
    call_model_func = create_call_model_with_tools(available_tools)

    # 创建 ToolNode（如果工具存在）
    if available_tools:
        tool_node = ToolNode(available_tools)
        logger.info(f"创建 ToolNode，包含 {len(available_tools)} 个工具")
    else:
        tool_node = None
        logger.info("没有可用工具，不创建 ToolNode")

    # 添加节点
    builder.add_node("agent", call_model_func)
    if tool_node:
        builder.add_node("tools", tool_node)

    # 设置入口
    builder.set_entry_point("agent")

    if tool_node:
        builder.add_conditional_edges(
            "agent",
            should_continue,
            {
                "tools": "tools",
                "end": END
            }
        )
        builder.add_edge("tools", "agent")
    else:
        builder.add_edge("agent", END)

    return builder.compile(checkpointer=checkpointer, store=store)