"""Dify Agent 节点工厂函数"""

from typing import Dict, Any, Callable
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from app.agent.state import AgentState
from app.services.dify.client import DifyClient
from app.services.dify.manager import DifyAgentConfig
from app.core.logger import logger


def create_dify_agent_node(agent_config: DifyAgentConfig) -> Callable:
    """
    动态创建 Dify Agent 节点函数

    Args:
        agent_config: Dify Agent 配置

    Returns:
        节点函数
    """

    async def dify_agent_node(
        state: AgentState,
        config: RunnableConfig,
    ) -> Dict[str, Any]:
        """
        Dify Agent 节点 - 调用 Dify API 并返回结果

        Args:
            state: Agent 状态
            config: 运行配置

        Returns:
            更新后的状态
        """
        try:
            messages = state["messages"]
            if not messages:
                logger.warning(f"Dify Agent '{agent_config.name}' 收到空消息列表")
                return {"messages": [AIMessage(content="没有收到消息")]}

            # 获取最后一条用户消息
            last_message = messages[-1]
            query = last_message.content if hasattr(last_message, "content") else str(last_message)

            # 获取用户 ID 和会话 ID
            user_id = config.get("configurable", {}).get("user_id", "default")
            conversation_id = config.get("configurable", {}).get("thread_id")

            logger.info(
                f"Dify Agent '{agent_config.name}' 处理消息: "
                f"user_id={user_id}, conversation_id={conversation_id}, "
                f"query={query[:100]}..."
            )

            # 创建 Dify 客户端
            client = DifyClient(
                base_url=agent_config.base_url,
                api_key=agent_config.api_key,
                timeout=agent_config.config.get("timeout", 60),
            )

            try:
                # 根据 Agent 类型调用不同的 API
                if agent_config.agent_type == "workflow":
                    # 工作流类型
                    inputs = agent_config.config.get("inputs", {})
                    inputs["query"] = query  # 将查询添加到输入中

                    result = await client.run_workflow(
                        inputs=inputs,
                        user_id=user_id,
                        response_mode="blocking",
                    )

                    # 提取工作流输出
                    if "data" in result and "outputs" in result["data"]:
                        output = result["data"]["outputs"]
                        # 尝试获取文本输出
                        if isinstance(output, dict):
                            response_text = output.get("text") or output.get("result") or str(output)
                        else:
                            response_text = str(output)
                    else:
                        response_text = str(result)

                else:
                    # Chatbot 或 Agent 类型
                    result = await client.chat(
                        query=query,
                        user_id=user_id,
                        conversation_id=conversation_id,
                        inputs=agent_config.config.get("inputs"),
                        response_mode="blocking",
                    )

                    # 提取回答
                    if "answer" in result:
                        response_text = result["answer"]
                    elif "data" in result and "answer" in result["data"]:
                        response_text = result["data"]["answer"]
                    else:
                        response_text = str(result)

                logger.info(
                    f"Dify Agent '{agent_config.name}' 返回结果: "
                    f"{response_text[:200]}..."
                )

                # 返回 AI 消息
                return {"messages": [AIMessage(content=response_text)]}

            finally:
                # 关闭客户端
                await client.close()

        except Exception as e:
            logger.error(
                f"Dify Agent '{agent_config.name}' 执行失败: {e}",
                exc_info=True
            )
            error_message = f"调用 Dify Agent '{agent_config.name}' 失败: {str(e)}"
            return {"messages": [AIMessage(content=error_message)]}

    # 设置函数名称,便于调试
    dify_agent_node.__name__ = f"dify_agent_{agent_config.name}"

    return dify_agent_node


def create_dify_agent_streaming_node(agent_config: DifyAgentConfig) -> Callable:
    """
    创建支持流式输出的 Dify Agent 节点

    注意: 流式节点需要特殊处理,暂时保留此函数作为未来扩展

    Args:
        agent_config: Dify Agent 配置

    Returns:
        流式节点函数
    """

    async def dify_agent_streaming_node(
        state: AgentState,
        config: RunnableConfig,
    ) -> Dict[str, Any]:
        """
        Dify Agent 流式节点 (未实现)

        流式输出需要在 Graph 层面支持,目前暂不实现
        """
        logger.warning(f"Dify Agent '{agent_config.name}' 流式节点暂未实现,使用阻塞模式")
        # 回退到阻塞模式
        blocking_node = create_dify_agent_node(agent_config)
        return await blocking_node(state, config)

    dify_agent_streaming_node.__name__ = f"dify_agent_streaming_{agent_config.name}"

    return dify_agent_streaming_node

