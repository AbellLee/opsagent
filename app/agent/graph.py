from typing import Dict, Any, Optional, List, Union
from langchain_core.messages import ToolMessage, AIMessage, HumanMessage, SystemMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.store.base import BaseStore
from langchain_core.runnables import RunnableConfig
from app.core.logger import logger
from app.agent.state import AgentState
from app.core.llm import get_llm, LLMInitializationError
import asyncio
import concurrent.futures
import time

def call_llm_with_timeout(llm, messages, timeout_seconds=90, stream=False):
    """
    带超时控制的LLM调用函数
    支持流式和非流式输出
    """
    def _call_llm():
        try:
            if hasattr(llm, 'dashscope_api_key') or type(llm).__name__ == 'Tongyi':
                # 对于Tongyi模型，使用字典格式
                formatted_messages = []
                for msg in messages:
                    if isinstance(msg, SystemMessage):
                        formatted_messages.append({"role": "system", "content": msg.content})
                    elif isinstance(msg, HumanMessage):
                        formatted_messages.append({"role": "user", "content": msg.content})
                    elif isinstance(msg, AIMessage):
                        formatted_messages.append({"role": "assistant", "content": msg.content})
                    else:
                        # 处理其他类型的消息
                        formatted_messages.append({"role": "user", "content": str(getattr(msg, 'content', str(msg)))})

                logger.info(f"调用Tongyi模型，消息数量: {len(formatted_messages)}, 流式模式: {stream}")

                if stream:
                    # 流式调用
                    return llm.stream(formatted_messages)
                else:
                    # 非流式调用
                    return llm.invoke(formatted_messages)
            else:
                # 对于其他模型，使用BaseMessage对象列表调用
                logger.info(f"调用OpenAI兼容模型，消息数量: {len(messages)}, 流式模式: {stream}")
                logger.info(f"模型配置 - base_url: {getattr(llm, 'base_url', 'N/A')}, model: {getattr(llm, 'model_name', getattr(llm, 'model', 'N/A'))}")
                logger.info(f"模型配置 - timeout: {getattr(llm, 'timeout', 'N/A')}, max_retries: {getattr(llm, 'max_retries', 'N/A')}")

                if stream:
                    # 流式调用
                    return llm.stream(messages)
                else:
                    # 非流式调用
                    response = llm.invoke(messages)
                    if hasattr(response, 'content'):
                        return response.content
                    else:
                        return str(response)
        except Exception as e:
            logger.error(f"LLM调用内部错误: {e}")
            raise

    if stream:
        # 流式模式：直接调用，不使用超时控制（因为流式输出需要逐步返回）
        logger.info(f"开始LLM流式调用")
        start_time = time.time()
        result = _call_llm()
        logger.info(f"LLM流式调用开始，耗时: {time.time() - start_time:.2f}秒")
        return result
    else:
        # 非流式模式：使用线程池执行器来实现超时控制
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(_call_llm)
            try:
                logger.info(f"开始LLM调用，超时设置: {timeout_seconds}秒")
                start_time = time.time()
                result = future.result(timeout=timeout_seconds)
                end_time = time.time()
                logger.info(f"LLM调用成功，耗时: {end_time - start_time:.2f}秒")
                return result
            except concurrent.futures.TimeoutError:
                logger.error(f"LLM调用超时（{timeout_seconds}秒），正在取消请求...")
                future.cancel()
                raise TimeoutError(f"模型调用超时，超过{timeout_seconds}秒")

# 定义节点函数
def call_model(state: AgentState, config: RunnableConfig, *, store: Optional[BaseStore] = None) -> Dict[str, Any]:
    """调用模型 - 支持流式输出"""
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

        # 准备消息
        messages: List[BaseMessage] = [SystemMessage(content=system_msg)]
        messages.extend(state["messages"])

        # 使用LLM进行调用，支持LangGraph的messages流式模式
        try:
            logger.info(f"开始调用模型，模型类型: {type(llm).__name__}")

            # 检查是否在流式上下文中
            from langgraph.config import get_stream_writer
            try:
                writer = get_stream_writer()
                logger.info("检测到流式上下文，使用流式调用")

                # 在流式上下文中，实时发送每个chunk
                full_content = ""
                for chunk in llm.stream(messages):
                    if hasattr(chunk, 'content') and chunk.content:
                        content = chunk.content
                        full_content += content
                        # logger.info(f"LLM产生chunk: {repr(content)}")

                        # 实时发送chunk到流式输出
                        writer(chunk)

                logger.info("流式模型调用成功")
                ai_message = AIMessage(content=full_content)

            except Exception as stream_error:
                logger.info(f"非流式上下文或流式调用失败: {stream_error}")

                # 回退到普通调用
                response = llm.invoke(messages)
                logger.info("模型调用成功")

                if hasattr(response, 'content'):
                    ai_message = AIMessage(content=response.content)
                else:
                    ai_message = AIMessage(content=str(response))

            return {"messages": [ai_message]}

        except Exception as e:
            logger.error(f"调用模型失败: {e}")
            return {"messages": [AIMessage(content=f"模型调用失败: {str(e)}")]}

    except Exception as e:
        logger.error(f"调用模型失败: {e}")
        return {"messages": [AIMessage(content=f"模型调用失败: {str(e)}")]}



# 构建图
def create_graph(checkpointer=None, store=None):
    """创建graph图"""
    from app.agent.state import AgentState

    # 创建graph
    builder = StateGraph(AgentState)

    # 添加节点
    builder.add_node("agent", call_model)

    # 设置入口点
    builder.set_entry_point("agent")

    # 添加边到结束点
    builder.add_edge("agent", END)

    return builder.compile(checkpointer=checkpointer, store=store)

