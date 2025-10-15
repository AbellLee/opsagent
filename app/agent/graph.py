from typing import Dict, Any, Optional, List
from langchain_core.messages import ToolMessage, AIMessage, HumanMessage, SystemMessage, BaseMessage
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph, END
from langgraph.store.base import BaseStore
from langgraph.prebuilt import ToolNode
from langchain_core.runnables import RunnableConfig
from app.core.logger import logger
from app.agent.state import AgentState
from app.core.llm import get_llm, LLMInitializationError


# ========================
# 异步节点函数：call_model
# ========================
def create_call_model_with_tools(tools: List[BaseTool]):
    """创建带工具的call_model函数（闭包）"""

    async def call_model(
        state: AgentState,
        config: RunnableConfig,
        *,
        store: Optional[BaseStore] = None
    ) -> Dict[str, Any]:
        """调用模型 - 支持工具调用和流式输出（异步版本）"""
        try:
            # 构建系统消息（支持长期记忆）
            system_msg = "你是一个智能助手"
            if store and "user_id" in config.get("configurable", {}):
                namespace = ("memories", config["configurable"]["user_id"])
                memories = store.search(namespace, query=str(state["messages"][-1].content))
                info = "\n".join([d.value["data"] for d in memories])
                if info:
                    system_msg = f"你是一个智能助手。相关信息: {info}"

            # 初始化 LLM
            try:
                llm, _ = get_llm()
            except LLMInitializationError as e:
                logger.error(f"LLM初始化失败: {e}")
                return {"messages": [AIMessage(content=f"模型初始化失败: {str(e)}")]}

            # 绑定工具到模型
            if tools:
                model_with_tools = llm.bind_tools(tools)
                logger.info(f"已绑定 {len(tools)} 个工具到模型")
            else:
                model_with_tools = llm
                logger.warning("未找到工具列表，使用无工具的模型")

            # 准备消息历史
            messages: List[BaseMessage] = [SystemMessage(content=system_msg)]
            messages.extend(state["messages"])

            logger.info(f"开始调用模型，模型类型: {type(model_with_tools).__name__}")

            # 尝试异步流式调用
            try:
                from langgraph.config import get_stream_writer
                writer = get_stream_writer()
                logger.info("检测到流式上下文，使用异步流式调用")

                full_response = None
                async for chunk in model_with_tools.astream(messages):
                    # LangGraph 的 writer 是同步可调用的
                    writer(chunk)
                    full_response = chunk if full_response is None else full_response + chunk

                ai_message = full_response
                logger.info("异步流式模型调用成功")

            except Exception as stream_error:
                # 回退到异步普通调用
                logger.info(f"非流式上下文或流式调用失败，回退到 ainvoke: {stream_error}")
                ai_message = await model_with_tools.ainvoke(messages)
                logger.info("异步模型调用成功")

            return {"messages": [ai_message]}

        except Exception as e:
            logger.error(f"调用模型失败: {e}", exc_info=True)
            return {"messages": [AIMessage(content=f"模型调用失败: {str(e)}")]}

    return call_model


# ========================
# 路由函数：should_continue
# ========================
def should_continue(state: AgentState) -> str:
    """决定是否继续执行工具"""
    messages = state["messages"]
    last_message = messages[-1]

    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        tool_names = [tc['name'] for tc in last_message.tool_calls]
        logger.info(f"检测到工具调用: {tool_names}")
        return "tools"

    logger.info("没有工具调用，结束对话")
    return "end"


# ========================
# 构建图：create_graph
# ========================
async def create_graph_async(checkpointer=None, store=None):
    """创建 graph 图（异步版本 - 支持MCP工具加载）"""
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