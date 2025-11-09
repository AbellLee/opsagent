"""Agent节点函数

包含LangGraph图中的节点函数，主要是call_model节点。
"""
from typing import Dict, Any, Optional, List
from langchain_core.messages import AIMessage, SystemMessage, BaseMessage
from langchain_core.tools import BaseTool
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore
from langgraph.types import interrupt
import os

from app.core.logger import get_logger
from app.agent.state import AgentState
from app.agent.agent_utils import get_llm_from_config, fix_incomplete_tool_calls
from app.core.llm import LLMInitializationError

# 使用模块级logger
logger = get_logger("agent.nodes")


def create_call_model_with_tools(tools: List[BaseTool]):
    """创建带工具的call_model函数（闭包）

    Args:
        tools: 可用工具列表

    Returns:
        call_model函数，用作LangGraph的节点函数

    Example:
        >>> tools = [SearchTool(), WeatherTool()]
        >>> call_model = create_call_model_with_tools(tools)
        >>> builder.add_node("agent", call_model)
    """

    async def call_model(
        state: AgentState,
        config: RunnableConfig,
        *,
        store: Optional[BaseStore] = None
    ) -> Dict[str, Any]:
        """调用模型 - 支持工具调用和流式输出（异步版本）
        
        Args:
            state: Agent状态，包含消息历史
            config: LangGraph配置对象
            store: 可选的长期记忆存储
        
        Returns:
            包含messages字段的字典，用于更新Agent状态
        
        Raises:
            Exception: 当模型调用失败时
        """
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
                logger.error(f"LLM初始化失败: {e}", exc_info=True)
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
                        logger.warning(f"绑定工具到模型时出错: {bind_error}，将使用无工具的模型", exc_info=True)
                        model_with_tools = llm
            else:
                model_with_tools = llm
                logger.warning("未找到工具列表，使用无工具的模型")
            
            # 准备消息历史
            messages: List[BaseMessage] = [SystemMessage(content=system_msg)]
            
            # 修复不完整的消息序列 - 确保所有tool_calls都有对应的ToolMessage
            fixed_messages = fix_incomplete_tool_calls(state["messages"])
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

                # 检查是否是通义千问的已知 bug
                error_msg = str(stream_error)
                if "list index out of range" in error_msg and "tool_calls" in error_msg:
                    logger.warning("检测到通义千问 tool_calls bug，尝试不使用工具重新调用")
                    # 使用不带工具的模型重试
                    try:
                        ai_message = await llm.ainvoke(messages)
                        logger.info("使用无工具模型调用成功")
                    except Exception as retry_error:
                        logger.error(f"重试失败: {retry_error}")
                        raise stream_error
                else:
                    ai_message = await model_with_tools.ainvoke(messages)
                    logger.info("异步模型调用成功")

            return {"messages": [ai_message]}

        except Exception as e:
            logger.error(f"调用模型失败: {e}", exc_info=True)

            # 提供更友好的错误消息
            error_type = type(e).__name__
            if "ConnectionError" in error_type or "ConnectionResetError" in str(e):
                error_msg = "模型调用失败: 网络连接中断，请稍后重试"
            elif "list index out of range" in str(e):
                error_msg = "模型调用失败: 模型响应格式错误（已知的通义千问 bug）"
            else:
                error_msg = f"模型调用失败: {str(e)}"

            return {"messages": [AIMessage(content=error_msg)]}

    return call_model

