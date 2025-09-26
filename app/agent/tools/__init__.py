from typing import List, Dict, Any, Optional
from langchain_core.tools import BaseTool
from app.agent.tools.mcp_tools import mcp_tool_manager
from app.agent.tools.custom_tools import get_custom_tools
from app.core.logger import logger
from app.core.config import settings
import psycopg2

class ToolManager:
    """工具管理器"""
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self._load_tools()
    
    def _load_tools(self):
        """加载所有工具"""
        # 加载MCP工具
        mcp_tools = mcp_tool_manager.register_mcp_tools()
        for tool in mcp_tools:
            self.tools[tool.name] = tool
            logger.info(f"已加载MCP工具: {tool.name}")
        
        # 加载自定义工具
        custom_tools = get_custom_tools()
        for tool in custom_tools:
            self.tools[tool.name] = tool
            logger.info(f"已加载自定义工具: {tool.name}")
    
    def get_tool(self, name: str) -> BaseTool:
        """根据名称获取工具"""
        return self.tools.get(name)
    
    def list_tools(self) -> List[Dict[str, str]]:
        """列出所有工具"""
        return [
            {
                "name": tool.name,
                "description": tool.description
            }
            for tool in self.tools.values()
        ]
    
    def _check_tool_approval(self, tool_name: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """检查工具是否需要审批"""
        try:
            conn = psycopg2.connect(settings.database_url)
            cursor = conn.cursor()
            
            # 首先检查用户特定配置
            if user_id:
                cursor.execute("""
                    SELECT auto_execute, approval_required 
                    FROM tool_approval_config 
                    WHERE user_id = %s AND tool_name = %s
                """, (user_id, tool_name))
                result = cursor.fetchone()
                if result:
                    return {
                        "auto_execute": result[0],
                        "approval_required": result[1]
                    }
            
            # 检查默认配置
            cursor.execute("""
                SELECT auto_execute, approval_required 
                FROM tool_approval_config 
                WHERE user_id IS NULL AND tool_name = %s
            """, (tool_name,))
            result = cursor.fetchone()
            if result:
                return {
                    "auto_execute": result[0],
                    "approval_required": result[1]
                }
            
            # 默认情况下需要审批
            return {
                "auto_execute": False,
                "approval_required": True
            }
        except Exception as e:
            logger.error(f"检查工具审批配置失败: {e}")
            # 出错时默认需要审批
            return {
                "auto_execute": False,
                "approval_required": True
            }
        finally:
            if 'conn' in locals():
                conn.close()
    
    def execute_tool(self, name: str, tool_input: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        """执行工具"""
        tool = self.get_tool(name)
        if not tool:
            return {
                "error": f"工具 '{name}' 未找到",
                "tool_name": name
            }
        
        # 检查是否需要审批
        approval_config = self._check_tool_approval(name, user_id)
        
        # 如果需要审批且不是自动执行，则返回待审批状态
        if approval_config["approval_required"] and not approval_config["auto_execute"]:
            return {
                "tool_name": name,
                "status": "pending_approval",
                "message": "工具执行需要人工审批",
                "tool_input": tool_input
            }
        
        # 直接执行工具
        try:
            result = tool.invoke(tool_input)
            return {
                "tool_name": name,
                "result": result,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"执行工具 '{name}' 失败: {e}")
            return {
                "error": str(e),
                "tool_name": name,
                "status": "error"
            }

# 全局工具管理器实例
tool_manager = ToolManager()