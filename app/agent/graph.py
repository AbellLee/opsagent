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
    """调用模型"""
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
            llm, embedding = get_llm()
        except LLMInitializationError as e:
            logger.error(f"LLM初始化失败: {e}")
            return {"messages": [AIMessage(content=f"模型初始化失败: {str(e)}")]}
        
        # 准备消息
        messages: List[BaseMessage] = [SystemMessage(content=system_msg)]
        messages.extend(state["messages"])
        
        # 调用模型（预判模型类型，避免运行时错误）
        try:
            # 检查是否是Tongyi模型
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
                
                response_content = llm.invoke(formatted_messages)
            else:
                # 对于其他模型，使用BaseMessage对象列表调用
                response = llm.invoke(messages)
                if hasattr(response, 'content'):
                    response_content = response.content
                else:
                    response_content = str(response)
        except Exception as e:
            logger.error(f"调用模型失败: {e}")
            raise
            
        response = AIMessage(content=response_content)
        return {"messages": [response]}
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