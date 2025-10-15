from typing import List, Dict, Any, Optional
from langchain_core.tools import BaseTool
from app.core.logger import logger
from app.services.mcp import mcp_config_service

try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
    MCP_AVAILABLE = True
except ImportError:
    logger.warning("langchain-mcp-adapters not installed. MCP tools will be disabled.")
    MCP_AVAILABLE = False

class MCPToolWrapper:
    """MCP工具包装器 - 使用LangGraph官方适配器"""

    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.mcp_client: Optional[MultiServerMCPClient] = None
        self.mcp_servers_config = self._load_mcp_servers_config()

    def _load_mcp_servers_config(self) -> Dict[str, Dict[str, Any]]:
        """从数据库加载MCP服务器配置"""
        try:
            # 从数据库获取启用的MCP配置
            config = mcp_config_service.get_enabled_configs_dict()

            if config:
                logger.info(f"从数据库加载MCP服务器配置: {list(config.keys())}")
            else:
                logger.info("数据库中未找到启用的MCP服务器配置")

            return config

        except Exception as e:
            logger.error(f"从数据库加载MCP配置失败: {e}")
            logger.info("将使用空配置")
            return {}

    async def _initialize_mcp_client(self) -> bool:
        """初始化MCP客户端"""
        if not MCP_AVAILABLE:
            logger.warning("MCP适配器不可用，跳过MCP客户端初始化")
            return False

        if not self.mcp_servers_config:
            logger.info("没有配置MCP服务器，跳过MCP客户端初始化")
            return False

        try:
            self.mcp_client = MultiServerMCPClient(self.mcp_servers_config)
            logger.info(f"MCP客户端初始化成功，连接到 {len(self.mcp_servers_config)} 个服务器")
            return True
        except Exception as e:
            logger.error(f"MCP客户端初始化失败: {e}")
            return False

    async def register_mcp_tools(self) -> List[BaseTool]:
        """从MCP服务器注册工具"""
        if not MCP_AVAILABLE:
            return []

        try:
            # 初始化MCP客户端
            if not self.mcp_client:
                success = await self._initialize_mcp_client()
                if not success:
                    return []

            # 获取所有MCP工具
            tools = await self.mcp_client.get_tools()

            # 缓存工具
            for tool in tools:
                self.tools[tool.name] = tool

            logger.info(f"成功注册 {len(tools)} 个MCP工具: {[tool.name for tool in tools]}")
            return tools

        except Exception as e:
            logger.error(f"注册MCP工具失败: {e}")
            return []

    def get_mcp_tool(self, tool_name: str) -> Optional[BaseTool]:
        """根据名称获取MCP工具"""
        return self.tools.get(tool_name)

    def list_mcp_tools(self) -> List[str]:
        """列出所有MCP工具名称"""
        return list(self.tools.keys())

    async def close(self):
        """关闭MCP客户端连接"""
        if self.mcp_client:
            try:
                # 注意: MultiServerMCPClient可能没有显式的close方法
                # 这里只是示例，实际实现可能需要根据具体API调整
                if hasattr(self.mcp_client, 'close'):
                    await self.mcp_client.close()
                logger.info("MCP客户端连接已关闭")
            except Exception as e:
                logger.error(f"关闭MCP客户端失败: {e}")

# 全局MCP工具管理器实例
mcp_tool_manager = MCPToolWrapper()