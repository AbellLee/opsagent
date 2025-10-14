from typing import Dict, Any, Optional, List, Union
from langchain_core.messages import ToolMessage, AIMessage, HumanMessage, SystemMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.store.base import BaseStore
from langgraph.prebuilt import ToolNode
from langchain_core.runnables import RunnableConfig
from app.core.logger import logger
from app.agent.state import AgentState
from app.core.llm import get_llm, LLMInitializationError
# 定义节点函数
def call_model(state: AgentState, config: RunnableConfig, *, store: Optional[BaseStore] = None) -> Dict[str, Any]:
    """调用模型 - 支持工具调用和流式输出"""
    try:
        # 检查是否需要使用长期记忆
        system_msg = "你是一个智能助手"
        if store and "user_id" in config.get("configurable", {}):
            # 实现长期记忆逻辑
            namespace = ("memories", config["configurable"]["user_id"])
            # 获取state中最新一条消息(用户问题)进行检索
            memories = store.search(namespace, query=str(state["messages"][-1].content))
            info = "\n".join([d.value["data"] for d in memories])
            # 将检索到的知识拼接到系统prompt
            if info:
                system_msg = f"你是一个智能助手。相关信息: {info}"

        # 初始化LLM
        try:
            llm, _ = get_llm()  # 不需要embedding，用_忽略
        except LLMInitializationError as e:
            logger.error(f"LLM初始化失败: {e}")
            return {"messages": [AIMessage(content=f"模型初始化失败: {str(e)}")]}

        # 获取可用工具并绑定到模型
        from app.agent.tools import tool_manager
        available_tools = tool_manager.get_all_tools()

        # 将工具绑定到模型
        if available_tools:
            model_with_tools = llm.bind_tools(available_tools)
            logger.info(f"已绑定 {len(available_tools)} 个工具到模型")
        else:
            model_with_tools = llm
            logger.info("没有可用工具，使用普通模型")

        # 准备消息
        messages: List[BaseMessage] = [SystemMessage(content=system_msg)]
        messages.extend(state["messages"])

        # 使用绑定了工具的模型进行调用，支持LangGraph的messages流式模式
        try:
            logger.info(f"开始调用模型，模型类型: {type(model_with_tools).__name__}")

            # 检查是否在流式上下文中
            from langgraph.config import get_stream_writer
            try:
                writer = get_stream_writer()
                logger.info("检测到流式上下文，使用流式调用")

                full_response = None
                for chunk in model_with_tools.stream(messages):
                    writer(chunk)
                    full_response = chunk if full_response is None else full_response + chunk

                ai_message = full_response  # 已包含 content 和 tool_calls
                logger.info("流式模型调用成功")

            except Exception as stream_error:
                logger.info(f"非流式上下文或流式调用失败: {stream_error}")
                ai_message = model_with_tools.invoke(messages)

            except Exception as stream_error:
                logger.info(f"非流式上下文或流式调用失败: {stream_error}")

                # 回退到普通调用
                response = model_with_tools.invoke(messages)
                logger.info("模型调用成功")

                if hasattr(response, 'content'):
                    ai_message = response  # 保持原始响应，包含可能的tool_calls
                else:
                    ai_message = AIMessage(content=str(response))

            return {"messages": [ai_message]}

        except Exception as e:
            logger.error(f"调用模型失败: {e}")
            return {"messages": [AIMessage(content=f"模型调用失败: {str(e)}")]}

    except Exception as e:
        logger.error(f"调用模型失败: {e}")
        return {"messages": [AIMessage(content=f"模型调用失败: {str(e)}")]}


def should_continue(state: AgentState) -> str:
    """决定是否继续执行工具"""
    messages = state["messages"]
    last_message = messages[-1]

    # 检查最后一条消息是否包含工具调用
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        logger.info(f"检测到工具调用: {[tc['name'] for tc in last_message.tool_calls]}")
        return "tools"

    logger.info("没有工具调用，结束对话")
    return "end"



# 构建图
def create_graph(checkpointer=None, store=None):
    """创建graph图 - 支持工具调用"""
    from app.agent.state import AgentState
    from app.agent.tools import tool_manager

    # 创建graph
    builder = StateGraph(AgentState)

    # 获取所有工具并创建ToolNode
    available_tools = tool_manager.get_all_tools()
    if available_tools:
        tool_node = ToolNode(available_tools)
        logger.info(f"创建ToolNode，包含 {len(available_tools)} 个工具")
    else:
        tool_node = None
        logger.info("没有可用工具，不创建ToolNode")

    # 添加节点
    builder.add_node("agent", call_model)
    if tool_node:
        builder.add_node("tools", tool_node)

    # 设置入口点
    builder.set_entry_point("agent")

    if tool_node:
        # 添加条件边：根据是否有工具调用决定下一步
        builder.add_conditional_edges(
            "agent",
            should_continue,
            {
                "tools": "tools",
                "end": END
            }
        )

        # 从工具节点回到agent节点
        builder.add_edge("tools", "agent")
    else:
        # 没有工具时直接结束
        builder.add_edge("agent", END)

    return builder.compile(checkpointer=checkpointer, store=store)

