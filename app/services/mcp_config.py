"""
MCP服务器配置管理服务
"""

from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
import psycopg2
import psycopg2.extras
import json
from datetime import datetime, timezone

from app.core.config import settings
from app.core.logger import logger
from app.models.schemas import MCPServerConfig, MCPServerConfigCreate, MCPServerConfigUpdate


class MCPConfigService:
    """MCP配置服务"""

    def __init__(self):
        self.db_url = settings.database_url

    def _get_connection(self):
        """获取数据库连接"""
        conn = psycopg2.connect(self.db_url)
        # 注册UUID适配器
        psycopg2.extras.register_uuid(conn_or_curs=conn)
        return conn

    def create_mcp_config(self, config_data: MCPServerConfigCreate) -> MCPServerConfig:
        """创建MCP服务器配置"""
        conn = None
        try:
            logger.info(f"开始创建MCP配置: {config_data.name}")
            conn = self._get_connection()
            cursor = conn.cursor()

            config_id = uuid4()
            now = datetime.now(timezone.utc)
            logger.info(f"生成配置ID: {config_id}, 时间: {now}")

            cursor.execute("""
                INSERT INTO mcp_server_configs (id, name, description, config, enabled, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id, name, description, config, enabled, created_at, updated_at
            """, (
                config_id,
                config_data.name,
                config_data.description,
                json.dumps(config_data.config),
                config_data.enabled,
                now,
                now
            ))

            result = cursor.fetchone()
            conn.commit()

            return MCPServerConfig(
                id=result[0],
                name=result[1],
                description=result[2],
                config=json.loads(result[3]) if isinstance(result[3], str) else result[3],
                enabled=result[4],
                created_at=result[5],
                updated_at=result[6]
            )

        except psycopg2.IntegrityError as e:
            if conn:
                conn.rollback()
            if "unique constraint" in str(e).lower():
                raise ValueError(f"MCP服务器名称 '{config_data.name}' 已存在")
            raise
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"创建MCP配置失败: {e}")
            raise
        finally:
            if conn:
                cursor.close()
                conn.close()

    def get_mcp_config(self, config_id: UUID) -> Optional[MCPServerConfig]:
        """根据ID获取MCP配置"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, name, description, config, enabled, created_at, updated_at
                FROM mcp_server_configs
                WHERE id = %s
            """, (config_id,))

            result = cursor.fetchone()
            if not result:
                return None

            return MCPServerConfig(
                id=result[0],
                name=result[1],
                description=result[2],
                config=json.loads(result[3]) if isinstance(result[3], str) else result[3],
                enabled=result[4],
                created_at=result[5],
                updated_at=result[6]
            )

        except Exception as e:
            logger.error(f"获取MCP配置失败: {e}")
            raise
        finally:
            if conn:
                cursor.close()
                conn.close()

    def get_mcp_config_by_name(self, name: str) -> Optional[MCPServerConfig]:
        """根据名称获取MCP配置"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, name, description, config, enabled, created_at, updated_at
                FROM mcp_server_configs
                WHERE name = %s
            """, (name,))

            result = cursor.fetchone()
            if not result:
                return None

            return MCPServerConfig(
                id=result[0],
                name=result[1],
                description=result[2],
                config=json.loads(result[3]) if isinstance(result[3], str) else result[3],
                enabled=result[4],
                created_at=result[5],
                updated_at=result[6]
            )

        except Exception as e:
            logger.error(f"获取MCP配置失败: {e}")
            raise
        finally:
            if conn:
                cursor.close()
                conn.close()

    def list_mcp_configs(self, enabled_only: bool = False) -> List[MCPServerConfig]:
        """列出所有MCP配置"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = """
                SELECT id, name, description, config, enabled, created_at, updated_at
                FROM mcp_server_configs
            """
            params = []

            if enabled_only:
                query += " WHERE enabled = %s"
                params.append(True)

            query += " ORDER BY created_at DESC"

            cursor.execute(query, params)
            results = cursor.fetchall()

            configs = []
            for result in results:
                configs.append(MCPServerConfig(
                    id=result[0],
                    name=result[1],
                    description=result[2],
                    config=json.loads(result[3]) if isinstance(result[3], str) else result[3],
                    enabled=result[4],
                    created_at=result[5],
                    updated_at=result[6]
                ))

            return configs

        except Exception as e:
            logger.error(f"列出MCP配置失败: {e}")
            raise
        finally:
            if conn:
                cursor.close()
                conn.close()

    def update_mcp_config(self, config_id: UUID, update_data: MCPServerConfigUpdate) -> Optional[MCPServerConfig]:
        """更新MCP配置"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # 构建更新字段
            update_fields = []
            params = []

            if update_data.name is not None:
                update_fields.append("name = %s")
                params.append(update_data.name)

            if update_data.description is not None:
                update_fields.append("description = %s")
                params.append(update_data.description)

            if update_data.config is not None:
                update_fields.append("config = %s")
                params.append(json.dumps(update_data.config))

            if update_data.enabled is not None:
                update_fields.append("enabled = %s")
                params.append(update_data.enabled)

            if not update_fields:
                # 没有要更新的字段，直接返回当前配置
                return self.get_mcp_config(config_id)

            update_fields.append("updated_at = %s")
            params.append(datetime.now(timezone.utc))
            params.append(config_id)

            query = f"""
                UPDATE mcp_server_configs
                SET {', '.join(update_fields)}
                WHERE id = %s
                RETURNING id, name, description, config, enabled, created_at, updated_at
            """

            cursor.execute(query, params)
            result = cursor.fetchone()

            if not result:
                return None

            conn.commit()

            return MCPServerConfig(
                id=result[0],
                name=result[1],
                description=result[2],
                config=json.loads(result[3]) if isinstance(result[3], str) else result[3],
                enabled=result[4],
                created_at=result[5],
                updated_at=result[6]
            )

        except psycopg2.IntegrityError as e:
            if conn:
                conn.rollback()
            if "unique constraint" in str(e).lower():
                raise ValueError(f"MCP服务器名称已存在")
            raise
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"更新MCP配置失败: {e}")
            raise
        finally:
            if conn:
                cursor.close()
                conn.close()

    def delete_mcp_config(self, config_id: UUID) -> bool:
        """删除MCP配置"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM mcp_server_configs
                WHERE id = %s
            """, (config_id,))

            deleted_count = cursor.rowcount
            conn.commit()

            return deleted_count > 0

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"删除MCP配置失败: {e}")
            raise
        finally:
            if conn:
                cursor.close()
                conn.close()

    def get_enabled_configs_dict(self) -> Dict[str, Dict[str, Any]]:
        """获取启用的MCP配置，返回字典格式用于MultiServerMCPClient"""
        configs = self.list_mcp_configs(enabled_only=True)
        result = {}
        
        for config in configs:
            result[config.name] = config.config
            
        logger.info(f"加载了 {len(result)} 个启用的MCP服务器配置: {list(result.keys())}")
        return result


# 全局MCP配置服务实例
mcp_config_service = MCPConfigService()
