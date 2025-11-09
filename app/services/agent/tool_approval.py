from typing import List, Dict, Any, Optional
import psycopg2
from psycopg2 import DatabaseError, OperationalError
from app.core.config import settings
from app.core.logger import get_logger

# 使用模块级logger
logger = get_logger("services.agent.tool_approval")


class ToolApprovalManager:
    """工具审批管理器"""

    def _check_tool_approval(self, tool_name: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """检查工具是否需要审批

        Args:
            tool_name: 工具名称
            user_id: 用户ID，为None时检查默认配置

        Returns:
            包含auto_execute和approval_required的字典

        Note:
            出错时默认需要审批（安全优先）
        """
        conn = None
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
                    logger.debug(f"找到用户 {user_id} 的工具 {tool_name} 配置")
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
                logger.debug(f"找到工具 {tool_name} 的默认配置")
                return {
                    "auto_execute": result[0],
                    "approval_required": result[1]
                }

            # 默认情况下需要审批
            logger.info(f"工具 {tool_name} 无配置，使用默认审批策略")
            return {
                "auto_execute": False,
                "approval_required": True
            }
        except (DatabaseError, OperationalError) as e:
            logger.error(f"数据库查询失败: {e}", exc_info=True)
            # 出错时默认需要审批（安全优先）
            return {
                "auto_execute": False,
                "approval_required": True
            }
        except Exception as e:
            logger.error(f"检查工具审批配置时发生未知错误: {e}", exc_info=True)
            # 出错时默认需要审批（安全优先）
            return {
                "auto_execute": False,
                "approval_required": True
            }
        finally:
            if conn is not None:
                conn.close()

    def execute_tool(self, name: str, tool_input: Dict[str, Any], tool_manager, user_id: Optional[str] = None) -> Dict[str, Any]:
        """执行工具

        Args:
            name: 工具名称
            tool_input: 工具输入参数
            tool_manager: 工具管理器实例
            user_id: 用户ID，用于检查审批配置

        Returns:
            包含执行结果的字典，可能的状态：
            - success: 执行成功
            - pending_approval: 等待审批
            - error: 执行失败
        """
        tool = tool_manager.get_tool(name)
        if not tool:
            logger.warning(f"工具 '{name}' 未找到")
            return {
                "error": f"工具 '{name}' 未找到",
                "tool_name": name,
                "status": "error"
            }

        # 检查是否需要审批
        approval_config = self._check_tool_approval(name, user_id)

        # 如果需要审批且不是自动执行，则返回待审批状态
        if approval_config["approval_required"] and not approval_config["auto_execute"]:
            logger.info(f"工具 '{name}' 需要人工审批")
            return {
                "tool_name": name,
                "status": "pending_approval",
                "message": "工具执行需要人工审批",
                "tool_input": tool_input
            }

        # 直接执行工具
        try:
            logger.info(f"开始执行工具 '{name}'")
            result = tool.invoke(tool_input)
            logger.info(f"工具 '{name}' 执行成功")
            return {
                "tool_name": name,
                "result": result,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"执行工具 '{name}' 失败: {e}", exc_info=True)
            return {
                "error": str(e),
                "tool_name": name,
                "status": "error"
            }