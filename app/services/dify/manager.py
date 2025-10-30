"""Dify Agent 管理器 - 负责加载、缓存和匹配 Dify Agent"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import psycopg2
import psycopg2.extras
from app.core.logger import logger
from app.core.config import settings


@dataclass
class DifyAgentConfig:
    """Dify Agent 配置"""
    id: str
    name: str
    description: Optional[str]
    agent_type: str  # 'chatbot', 'workflow', 'agent'
    dify_app_id: str
    api_key: str
    base_url: str
    capabilities: List[str]
    keywords: List[str]
    config: Dict[str, Any]
    input_schema: Optional[Dict[str, Any]]  # inputs 参数的 Schema 定义
    enabled: bool
    priority: int
    created_at: datetime
    updated_at: datetime


class DifyAgentManager:
    """Dify Agent 管理器"""

    def __init__(self, cache_ttl: int = 300):
        """
        初始化管理器

        Args:
            cache_ttl: 缓存过期时间(秒),默认 300 秒
        """
        self.cache_ttl = cache_ttl
        self.db_url = settings.database_url
        self._agents_cache: Optional[List[DifyAgentConfig]] = None
        self._cache_time: Optional[datetime] = None
        self._lock = asyncio.Lock()
        logger.info(f"Dify Agent Manager 初始化,缓存 TTL: {cache_ttl}秒")

    def _get_connection(self):
        """获取数据库连接"""
        conn = psycopg2.connect(self.db_url)
        psycopg2.extras.register_uuid(conn_or_curs=conn)
        return conn

    async def load_agents(self, force_reload: bool = False) -> List[DifyAgentConfig]:
        """
        从数据库加载 Dify Agent 配置

        Args:
            force_reload: 是否强制重新加载

        Returns:
            Dify Agent 配置列表
        """
        async with self._lock:
            # 检查缓存是否有效
            if not force_reload and self._is_cache_valid():
                logger.debug(f"使用缓存的 Dify Agent 配置,共 {len(self._agents_cache)} 个")
                return self._agents_cache

            # 从数据库加载
            try:
                conn = self._get_connection()
                try:
                    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                    cursor.execute("""
                        SELECT
                            id, name, description, agent_type, dify_app_id,
                            api_key, base_url, capabilities, keywords, config,
                            input_schema, enabled, priority, created_at, updated_at
                        FROM dify_agents
                        WHERE enabled = true
                        ORDER BY priority DESC, created_at ASC
                    """)

                    rows = cursor.fetchall()
                    agents = []
                    for row in rows:
                        agent = DifyAgentConfig(
                            id=str(row["id"]),
                            name=row["name"],
                            description=row["description"],
                            agent_type=row["agent_type"],
                            dify_app_id=row["dify_app_id"],
                            api_key=row["api_key"],
                            base_url=row["base_url"],
                            capabilities=row["capabilities"] or [],
                            keywords=row["keywords"] or [],
                            config=row["config"] or {},
                            input_schema=row["input_schema"],
                            enabled=row["enabled"],
                            priority=row["priority"],
                            created_at=row["created_at"],
                            updated_at=row["updated_at"],
                        )
                        agents.append(agent)

                    # 更新缓存
                    self._agents_cache = agents
                    self._cache_time = datetime.now()

                    logger.info(f"从数据库加载了 {len(agents)} 个 Dify Agent 配置")
                    return agents

                finally:
                    cursor.close()
                    conn.close()

            except Exception as e:
                logger.error(f"加载 Dify Agent 配置失败: {e}", exc_info=True)
                # 如果有缓存,返回缓存
                if self._agents_cache:
                    logger.warning("使用过期的缓存数据")
                    return self._agents_cache
                return []

    def _is_cache_valid(self) -> bool:
        """检查缓存是否有效"""
        if self._agents_cache is None or self._cache_time is None:
            return False

        elapsed = (datetime.now() - self._cache_time).total_seconds()
        return elapsed < self.cache_ttl

    async def get_agent_by_name(self, name: str) -> Optional[DifyAgentConfig]:
        """
        根据名称获取 Agent 配置

        Args:
            name: Agent 名称

        Returns:
            Agent 配置,如果不存在返回 None
        """
        agents = await self.load_agents()
        for agent in agents:
            if agent.name == name:
                return agent
        return None

    async def get_agent_by_id(self, agent_id: str) -> Optional[DifyAgentConfig]:
        """
        根据 ID 获取 Agent 配置

        Args:
            agent_id: Agent ID

        Returns:
            Agent 配置,如果不存在返回 None
        """
        agents = await self.load_agents()
        for agent in agents:
            if agent.id == agent_id:
                return agent
        return None

    async def match_agent(self, query: str, top_k: int = 1) -> List[DifyAgentConfig]:
        """
        根据查询匹配最合适的 Agent

        Args:
            query: 用户查询
            top_k: 返回前 k 个匹配的 Agent

        Returns:
            匹配的 Agent 列表,按优先级排序
        """
        agents = await self.load_agents()
        if not agents:
            return []

        # 简单的关键词匹配算法
        scored_agents = []
        query_lower = query.lower()

        for agent in agents:
            score = 0

            # 关键词匹配
            for keyword in agent.keywords:
                if keyword.lower() in query_lower:
                    score += 10

            # 能力匹配
            for capability in agent.capabilities:
                if capability.lower() in query_lower:
                    score += 5

            # 名称匹配
            if agent.name.lower() in query_lower:
                score += 20

            # 描述匹配
            if agent.description and agent.description.lower() in query_lower:
                score += 3

            if score > 0:
                scored_agents.append((agent, score))

        # 按分数和优先级排序
        scored_agents.sort(key=lambda x: (x[1], x[0].priority), reverse=True)

        # 返回前 k 个
        matched = [agent for agent, score in scored_agents[:top_k]]
        
        if matched:
            logger.info(f"为查询 '{query[:50]}...' 匹配到 {len(matched)} 个 Dify Agent")
        
        return matched

    async def refresh_cache(self):
        """手动刷新缓存"""
        logger.info("手动刷新 Dify Agent 配置缓存")
        await self.load_agents(force_reload=True)

    async def create_agent(
        self,
        name: str,
        agent_type: str,
        dify_app_id: str,
        api_key: str,
        base_url: str = "https://api.dify.ai/v1",
        description: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None,
        input_schema: Optional[Dict[str, Any]] = None,
        priority: int = 0,
        created_by: Optional[str] = None,
    ) -> str:
        """
        创建新的 Dify Agent 配置

        Returns:
            新创建的 Agent ID
        """
        try:
            conn = self._get_connection()
            try:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cursor.execute("""
                    INSERT INTO dify_agents (
                        name, description, agent_type, dify_app_id, api_key, base_url,
                        capabilities, keywords, config, input_schema, priority, created_by
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (name, description, agent_type, dify_app_id, api_key, base_url,
                      capabilities or [], keywords or [], psycopg2.extras.Json(config or {}),
                      psycopg2.extras.Json(input_schema) if input_schema else None,
                      priority, created_by))

                row = cursor.fetchone()
                agent_id = str(row["id"])
                conn.commit()

                logger.info(f"创建 Dify Agent 配置成功: {name} (ID: {agent_id})")

                # 刷新缓存
                await self.refresh_cache()

                return agent_id

            finally:
                cursor.close()
                conn.close()

        except Exception as e:
            logger.error(f"创建 Dify Agent 配置失败: {e}", exc_info=True)
            raise

    async def update_agent(
        self,
        agent_id: str,
        **kwargs
    ) -> bool:
        """
        更新 Dify Agent 配置

        Returns:
            是否更新成功
        """
        # 构建更新字段
        update_fields = []
        values = []

        allowed_fields = [
            "name", "description", "agent_type", "dify_app_id", "api_key", "base_url",
            "capabilities", "keywords", "config", "input_schema", "enabled", "priority"
        ]

        for field in allowed_fields:
            if field in kwargs:
                update_fields.append(f"{field} = %s")
                # 特殊处理 JSONB 字段
                if field in ["config", "input_schema"]:
                    values.append(psycopg2.extras.Json(kwargs[field]) if kwargs[field] else None)
                else:
                    values.append(kwargs[field])

        if not update_fields:
            logger.warning("没有需要更新的字段")
            return False

        # 添加 updated_at
        update_fields.append("updated_at = %s")
        values.append(datetime.now())

        # 添加 agent_id
        values.append(agent_id)

        try:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(f"""
                    UPDATE dify_agents
                    SET {', '.join(update_fields)}
                    WHERE id = %s
                """, values)

                success = cursor.rowcount == 1
                conn.commit()

                if success:
                    logger.info(f"更新 Dify Agent 配置成功: {agent_id}")
                    await self.refresh_cache()
                else:
                    logger.warning(f"Dify Agent 不存在: {agent_id}")

                return success

            finally:
                cursor.close()
                conn.close()

        except Exception as e:
            logger.error(f"更新 Dify Agent 配置失败: {e}", exc_info=True)
            raise


# 全局单例
_dify_manager: Optional[DifyAgentManager] = None


def get_dify_manager(cache_ttl: int = 300) -> DifyAgentManager:
    """获取 Dify Agent 管理器单例"""
    global _dify_manager
    if _dify_manager is None:
        _dify_manager = DifyAgentManager(cache_ttl=cache_ttl)
    return _dify_manager

