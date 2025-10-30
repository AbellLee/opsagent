"""Dify Agent 工具 - 将 Dify Agent 包装成 LangChain 工具"""

from typing import List, Optional, Type
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from app.core.logger import logger


class DifyAgentInput(BaseModel):
    """Dify Agent 工具的输入参数（基础版本）"""
    query: str = Field(description="要发送给 Dify Agent 的查询内容")
    conversation_id: Optional[str] = Field(
        default=None,
        description="会话 ID，用于多轮对话上下文（可选）"
    )
    inputs: Optional[dict] = Field(
        default=None,
        description="传入 Dify App 定义的变量值（可选）。例如: {'department': 'IT', 'priority': 'high'}"
    )


class DifyAgentTool(BaseTool):
    """Dify Agent 工具基类"""
    
    name: str
    description: str
    args_schema: Type[BaseModel] = DifyAgentInput
    
    # Dify Agent 配置
    agent_config: dict = Field(default_factory=dict)
    
    def _run(self, query: str, conversation_id: Optional[str] = None) -> str:
        """同步调用（不支持）"""
        raise NotImplementedError("Dify Agent 工具只支持异步调用")
    
    async def _arun(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        run_manager=None
    ) -> str:
        """异步调用 Dify Agent"""
        try:
            from app.services.dify.client import DifyClient
            
            # 创建 Dify 客户端
            client = DifyClient(
                base_url=self.agent_config.get("base_url", "https://api.dify.ai/v1"),
                api_key=self.agent_config["api_key"],
                timeout=self.agent_config.get("timeout", 60),
            )
            
            try:
                agent_type = self.agent_config.get("agent_type", "chatbot")
                
                # 根据 Agent 类型调用不同的 API
                if agent_type == "workflow":
                    # 工作流类型
                    inputs = self.agent_config.get("inputs", {})
                    inputs["query"] = query
                    
                    result = await client.run_workflow(
                        inputs=inputs,
                        user_id="default",
                        response_mode="blocking",
                    )
                    
                    # 提取工作流输出
                    if "data" in result and "outputs" in result["data"]:
                        output = result["data"]["outputs"]
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
                        user_id="default",
                        conversation_id=conversation_id,
                        inputs=self.agent_config.get("inputs"),
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
                    f"Dify Agent 工具 '{self.name}' 返回结果: "
                    f"{response_text[:200]}..."
                )
                
                return response_text
                
            finally:
                # 关闭客户端
                await client.close()
                
        except Exception as e:
            error_msg = f"调用 Dify Agent '{self.name}' 失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg


class DifyToolManager:
    """Dify Agent 工具管理器"""
    
    def __init__(self):
        self._tools_cache: Optional[List[BaseTool]] = None
        self._cache_timestamp: Optional[float] = None
        self._cache_ttl = 300  # 缓存 5 分钟
    
    async def get_dify_tools(self, force_reload: bool = False) -> List[BaseTool]:
        """
        获取所有 Dify Agent 工具
        
        Args:
            force_reload: 是否强制重新加载
            
        Returns:
            Dify Agent 工具列表
        """
        import time
        
        # 检查缓存
        if not force_reload and self._tools_cache is not None:
            if self._cache_timestamp and (time.time() - self._cache_timestamp) < self._cache_ttl:
                logger.info(f"使用缓存的 Dify 工具: {len(self._tools_cache)} 个")
                return self._tools_cache
        
        # 加载 Dify Agent 配置
        try:
            from app.services.dify.manager import get_dify_manager
            
            dify_manager = get_dify_manager()
            agents = await dify_manager.load_agents()
            
            if not agents:
                logger.info("没有可用的 Dify Agent 配置")
                self._tools_cache = []
                self._cache_timestamp = time.time()
                return []
            
            # 将每个 Dify Agent 转换为工具
            tools = []
            for agent in agents:
                # 构建工具描述
                tool_description = agent.description or f"调用 {agent.name}"
                
                # 添加能力和关键词信息到描述中
                if agent.capabilities:
                    tool_description += f"\n能力: {', '.join(agent.capabilities)}"
                if agent.keywords:
                    tool_description += f"\n适用场景: {', '.join(agent.keywords)}"
                
                # 创建工具实例
                tool = DifyAgentTool(
                    name=f"dify_{agent.name}",
                    description=tool_description,
                    agent_config={
                        "agent_type": agent.agent_type,
                        "base_url": agent.base_url,
                        "api_key": agent.api_key,
                        "inputs": agent.config.get("inputs"),
                        "timeout": agent.config.get("timeout", 60),
                    }
                )
                
                tools.append(tool)
                logger.info(f"创建 Dify 工具: {tool.name}")
            
            # 更新缓存
            self._tools_cache = tools
            self._cache_timestamp = time.time()
            
            logger.info(f"加载了 {len(tools)} 个 Dify Agent 工具")
            return tools
            
        except Exception as e:
            logger.error(f"加载 Dify Agent 工具失败: {e}", exc_info=True)
            return []
    
    async def refresh_cache(self):
        """刷新工具缓存"""
        logger.info("刷新 Dify 工具缓存")
        return await self.get_dify_tools(force_reload=True)


# 全局 Dify 工具管理器实例
dify_tool_manager = DifyToolManager()

