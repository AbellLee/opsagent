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
from langgraph.types import interrupt
import os


def get_llm_from_config(config: RunnableConfig):
    """
    从配置中获取 LLM 实例

    优先级：
    1. 如果配置中指定了 model_config_id，使用数据库配置
    2. 否则使用默认的 get_llm()（环境变量配置）

    Args:
        config: LangGraph 配置对象

    Returns:
        tuple: (llm, embedding) LLM 和嵌入模型实例
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
            logger.warning(f"使用数据库配置失败: {e}，回退到默认配置")
            # 回退到默认配置
            return get_llm()
    else:
        # 使用默认配置（环境变量）
        return get_llm()


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
            # 检查是否有中断请求
            thread_id = config.get("configurable", {}).get("thread_id")
            if thread_id:
                # 将导入移到函数内部以避免循环导入
                from app.services.agent.interrupt_service import get_interrupt_service
                interrupt_service = get_interrupt_service()
                if interrupt_service.check_interrupt_requested(thread_id):
                    reason = interrupt_service.get_interrupt_reason(thread_id)
                    logger.info(f"检测到中断请求，中断对话: session_id={thread_id}, reason={reason}")
                    # 清除中断状态
                    interrupt_service.clear_interrupt(thread_id)
                    # 触发中断
                    interrupt(f"用户中断了对话: {reason}")

            # 构建系统消息（支持长期记忆）
            system_msg = "你是一个智能助手"
            if store and "user_id" in config.get("configurable", {}):
                namespace = ("memories", config["configurable"]["user_id"])
                memories = store.search(namespace, query=str(state["messages"][-1].content))
                info = "\n".join([d.value["data"] for d in memories])
                if info:
                    system_msg = f"你是一个智能助手。相关信息: {info}"

            # 初始化 LLM（支持从配置中读取 model_config_id）
            try:
                llm, _ = get_llm_from_config(config)
            except LLMInitializationError as e:
                logger.error(f"LLM初始化失败: {e}")
                # 即使LLM初始化失败，也要返回状态，确保中断时能看到部分结果
                return {"messages": [AIMessage(content=f"模型初始化失败: {str(e)}")]}

            # 绑定工具到模型
            if tools:
                # 针对vLLM的特殊处理，避免使用"auto"工具选择模式
                # 因为vLLM需要额外的服务器端配置才能支持"auto"模式
                from app.core.config import settings
                llm_type = getattr(settings, 'llm_type', os.getenv("LLM_TYPE", "tongyi"))
                
                # 对于vLLM，暂时不使用工具，因为存在JSON格式问题
                if llm_type == "vllm":
                    model_with_tools = llm
                    logger.info("使用vLLM，暂时不绑定工具以避免JSON格式问题")
                else:
                    try:
                        model_with_tools = llm.bind_tools(tools)
                        logger.info(f"已绑定 {len(tools)} 个工具到模型")
                    except Exception as bind_error:
                        logger.warning(f"绑定工具到模型时出错: {bind_error}，将使用无工具的模型")
                        model_with_tools = llm
            else:
                model_with_tools = llm
                logger.warning("未找到工具列表，使用无工具的模型")

            # 准备消息历史
            messages: List[BaseMessage] = [SystemMessage(content=system_msg)]
            
            # 修复不完整的消息序列 - 确保所有tool_calls都有对应的ToolMessage
            fixed_messages = _fix_incomplete_tool_calls(state["messages"])
            messages.extend(fixed_messages)

            logger.info(f"开始调用模型，模型类型: {type(model_with_tools).__name__}")

            # 尝试异步流式调用
            try:
                from langgraph.config import get_stream_writer
                writer = get_stream_writer()
                logger.info("检测到流式上下文，使用异步流式调用")

                full_response = None
                accumulated_content = ""
                try:
                    async for chunk in model_with_tools.astream(messages):
                        # 检查是否有中断请求（在流式输出过程中）
                        if thread_id:
                            # 将导入移到函数内部以避免循环导入
                            from app.services.agent.interrupt_service import get_interrupt_service
                            interrupt_service = get_interrupt_service()
                            if interrupt_service.check_interrupt_requested(thread_id):
                                reason = interrupt_service.get_interrupt_reason(thread_id)
                                logger.info(f"检测到中断请求，中断流式输出: session_id={thread_id}, reason={reason}")
                                
                                # 在中断前，将已累积的内容作为最终消息
                                if accumulated_content:
                                    ai_message = AIMessage(content=accumulated_content)
                                    # 清除中断状态
                                    interrupt_service.clear_interrupt(thread_id)
                                    # 返回已累积的内容
                                    return {"messages": [ai_message]}
                                
                                # 清除中断状态
                                interrupt_service.clear_interrupt(thread_id)
                                # 触发中断
                                interrupt(f"用户中断了对话: {reason}")

                        # LangGraph 的 writer 是同步可调用的
                        writer(chunk)
                        full_response = chunk if full_response is None else full_response + chunk
                        
                        # 累积内容
                        if hasattr(chunk, 'content'):
                            accumulated_content += chunk.content

                    ai_message = full_response
                    logger.info("异步流式模型调用成功")

                except Exception as stream_error:
                    # 如果在流式传输过程中发生中断或其他错误，但已有累积内容，则返回它
                    if accumulated_content:
                        logger.info("流式传输过程中发生错误，但已有累积内容，返回累积内容")
                        ai_message = AIMessage(content=accumulated_content)
                    else:
                        raise stream_error

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


def _fix_incomplete_tool_calls(messages: List[BaseMessage]) -> List[BaseMessage]:
    """
    修复不完整的消息序列，确保所有包含tool_calls的AIMessage都有对应的ToolMessage
    
    当从检查点恢复对话时，可能存在包含tool_calls但没有对应ToolMessage的AIMessage，
    这会导致API错误。此函数会检测这种情况并添加占位的ToolMessage。
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