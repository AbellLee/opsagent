from typing import List, Dict, Any, Optional
from langchain_core.tools import BaseTool
from app.services.agent.tool_manager import ToolManager, MCPManager
from app.services.agent.tool_approval import ToolApprovalManager

# 全局管理器实例
tool_manager = ToolManager()
mcp_manager = MCPManager()
approval_manager = ToolApprovalManager()

__all__ = ["tool_manager", "mcp_manager", "approval_manager"]