from typing import List, Dict, Any, Optional
from langchain_core.tools import BaseTool
from app.agent.tools.custom_tools import get_custom_tools
from app.agent.tools.mcp_tools import mcp_tool_manager
from app.core.logger import logger


class ToolManager:
    """自定义工具管理器 - 只管理自定义工具"""

    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self._load_custom_tools()

    def _load_custom_tools(self):
        """加载自定义工具"""
        custom_tools = get_custom_tools()
        for tool in custom_tools:
            self.tools[tool.name] = tool
            logger.info(f"已加载自定义工具: {tool.name}")

        logger.info(f"自定义工具加载完成，共加载 {len(self.tools)} 个工具")

    def get_all_tools(self) -> List[BaseTool]:
        """获取所有自定义工具"""
        return list(self.tools.values())
        
    def get_tool(self, name: str) -> BaseTool:
        """根据名称获取自定义工具"""
        return self.tools.get(name)

    def list_tools(self) -> List[Dict[str, str]]:
        """列出所有自定义工具"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "type": "Custom"
            }
            for tool in self.tools.values()
        ]


class MCPManager:
    """MCP工具管理器 - 专门管理MCP工具"""

    def __init__(self):
        self.mcp_tool_manager = mcp_tool_manager

    async def get_mcp_tools(self) -> List[BaseTool]:
        """异步获取MCP工具"""
        try:
            tools = await self.mcp_tool_manager.register_mcp_tools()
            logger.info(f"MCP工具加载成功，共 {len(tools)} 个工具")
            return tools
        except Exception as e:
            logger.error(f"加载MCP工具失败: {e}")
            return []

    async def reload_mcp_tools(self) -> Dict[str, Any]:
        """重新加载MCP工具"""
        try:
            logger.info("开始重新加载MCP工具...")

            # 重新加载MCP配置
            self.mcp_tool_manager.mcp_servers_config = self.mcp_tool_manager._load_mcp_servers_config()
            self.mcp_tool_manager.mcp_client = None  # 重置客户端
            self.mcp_tool_manager.tools.clear()  # 清空缓存

            # 加载新工具
            tools = await self.get_mcp_tools()

            return {
                "success": True,
                "message": "MCP工具重新加载成功",
                "mcp_tools_count": len(tools),
                "mcp_tools": [tool.name for tool in tools]
            }

        except Exception as e:
            logger.error(f"重新加载MCP工具失败: {e}")
            return {
                "success": False,
                "message": f"重新加载MCP工具失败: {str(e)}",
                "error": str(e)
            }

    def list_mcp_tools(self) -> List[str]:
        """列出MCP工具名称"""
        return self.mcp_tool_manager.list_mcp_tools()