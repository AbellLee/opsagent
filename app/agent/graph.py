from typing import Dict, Any, Optional, List, Union
from langchain_core.messages import ToolMessage, AIMessage, HumanMessage, SystemMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.store.base import BaseStore
from langchain_core.runnables import RunnableConfig
from app.core.logger import logger
from app.agent.state import AgentState
from app.core.llm import get_llm, LLMInitializationError
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

