from typing import List, Dict, Any, Optional
from langchain_core.tools import BaseTool
from app.core.logger import logger
from app.services.mcp import mcp_config_service
import asyncio

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
            logger.info("开始从数据库加载MCP服务器配置...")
            # 从数据库获取启用的MCP配置
            config = mcp_config_service.get_enabled_configs_dict()

            if config:
                logger.info(f"从数据库加载MCP服务器配置: {list(config.keys())}")
                for name, cfg in config.items():
                    logger.info(f"配置 '{name}': {cfg}")
            else:
                logger.info("数据库中未找到启用的MCP服务器配置")

            return config

        except Exception as e:
            logger.error(f"从数据库加载MCP配置失败: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
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
            logger.info(f"正在初始化MCP客户端，配置: {self.mcp_servers_config}")

            # 验证配置格式
            for name, config in self.mcp_servers_config.items():
                if not isinstance(config, dict):
                    raise ValueError(f"配置 '{name}' 必须是字典格式")
                if "transport" not in config:
                    raise ValueError(f"配置 '{name}' 缺少必需的 'transport' 字段")

                transport = config["transport"]
                if transport == "stdio":
                    if "command" not in config:
                        raise ValueError(f"stdio配置 '{name}' 缺少 'command' 字段")
                    if "args" not in config:
                        raise ValueError(f"stdio配置 '{name}' 缺少 'args' 字段")
                elif transport == "streamable_http":
                    if "url" not in config:
                        raise ValueError(f"http配置 '{name}' 缺少 'url' 字段")
                else:
                    logger.warning(f"配置 '{name}' 使用了未知的传输类型: {transport}")

            self.mcp_client = MultiServerMCPClient(self.mcp_servers_config)
            logger.info(f"MCP客户端初始化成功，连接到 {len(self.mcp_servers_config)} 个服务器")
            return True
        except Exception as e:
            logger.error(f"MCP客户端初始化失败: {e}")
            logger.error(f"错误类型: {type(e).__name__}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return False

    async def register_mcp_tools(self) -> List[BaseTool]:
        """从MCP服务器注册工具"""
        if not MCP_AVAILABLE:
            logger.info("MCP适配器不可用，跳过工具注册")
            return []

        try:
            # 重新加载配置（确保获取最新的启用状态）
            self.mcp_servers_config = self._load_mcp_servers_config()

            # 初始化MCP客户端
            if not self.mcp_client:
                success = await self._initialize_mcp_client()
                if not success:
                    logger.warning("MCP客户端初始化失败，无法注册工具")
                    return []

            logger.info("开始获取MCP工具...")
            # 获取所有MCP工具，使用超时机制
            try:
                # 设置30秒超时
                tools = await asyncio.wait_for(
                    self.mcp_client.get_tools(),
                    timeout=30.0
                )
                logger.info(f"从MCP服务器获取到 {len(tools)} 个工具")
            except asyncio.TimeoutError:
                logger.error("获取MCP工具超时（30秒），可能是服务器响应慢或无法连接")
                self.mcp_client = None
                return []
            except Exception as tool_error:
                # 特别处理TaskGroup错误
                if "TaskGroup" in str(tool_error) or "unhandled errors" in str(tool_error):
                    logger.error("检测到TaskGroup错误，这可能是MCP服务器连接问题")
                    logger.error("建议检查MCP服务器配置和服务器状态")
                    # 尝试重置客户端
                    self.mcp_client = None
                raise tool_error

            # 缓存工具
            for tool in tools:
                self.tools[tool.name] = tool
                logger.debug(f"缓存工具: {tool.name}")

            logger.info(f"成功注册 {len(tools)} 个MCP工具: {[tool.name for tool in tools]}")
            return tools

        except Exception as e:
            logger.error(f"注册MCP工具失败: {e}")
            logger.error(f"错误类型: {type(e).__name__}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return []

    def get_mcp_tool(self, tool_name: str) -> Optional[BaseTool]:
        """根据名称获取MCP工具"""
        return self.tools.get(tool_name)

    def list_mcp_tools(self) -> List[str]:
        """列出所有MCP工具名称"""
        return list(self.tools.keys())

    async def test_config_validity(self) -> Dict[str, Any]:
        """测试配置有效性"""
        result = {
            "config_loaded": False,
            "config_count": 0,
            "config_details": {},
            "errors": []
        }

        try:
            config = self._load_mcp_servers_config()
            result["config_loaded"] = True
            result["config_count"] = len(config)
            result["config_details"] = config

            # 验证每个配置的必需字段
            for name, cfg in config.items():
                if "transport" not in cfg:
                    result["errors"].append(f"配置 '{name}' 缺少 'transport' 字段")
                elif cfg["transport"] == "stdio":
                    if "command" not in cfg:
                        result["errors"].append(f"stdio配置 '{name}' 缺少 'command' 字段")
                    if "args" not in cfg:
                        result["errors"].append(f"stdio配置 '{name}' 缺少 'args' 字段")
                elif cfg["transport"] == "streamable_http":
                    if "url" not in cfg:
                        result["errors"].append(f"http配置 '{name}' 缺少 'url' 字段")

        except Exception as e:
            result["errors"].append(f"配置加载失败: {str(e)}")

        return result

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