"""Dify API 客户端"""

import httpx
from typing import Dict, Any, Optional, AsyncIterator
from app.core.logger import logger


class DifyClient:
    """Dify API 客户端,支持 Chat 和 Workflow 调用"""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: int = 60,
    ):
        """
        初始化 Dify 客户端

        Args:
            base_url: Dify API 基础 URL (例如: https://api.dify.ai/v1 或 https://wsc-dify.300624.cn/)
            api_key: Dify API Key
            timeout: 请求超时时间(秒)
        """
        # 规范化 base_url
        # 如果已经包含 /v1，则去掉尾部斜杠
        # 如果不包含 /v1，则添加 /v1
        base_url = base_url.rstrip("/")
        if not base_url.endswith("/v1"):
            base_url = f"{base_url}/v1"

        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """获取或创建 HTTP 客户端"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def close(self):
        """关闭客户端连接"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def chat(
        self,
        query: str,
        user_id: str,
        conversation_id: Optional[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
        response_mode: str = "blocking",
        files: Optional[list] = None,
    ) -> Dict[str, Any]:
        """
        调用 Dify Chat API (阻塞模式)

        Args:
            query: 用户查询
            user_id: 用户 ID
            conversation_id: 会话 ID (可选)
            inputs: 额外输入参数
            response_mode: 响应模式 ('blocking' 或 'streaming')
            files: 文件列表 (可选)

        Returns:
            API 响应结果
        """
        client = await self._get_client()
        url = f"{self.base_url}/chat-messages"

        payload = {
            "query": query,
            "user": user_id,
            "response_mode": response_mode,
            "inputs": inputs if inputs is not None else {},  # inputs 是必需参数
        }

        if conversation_id:
            payload["conversation_id"] = conversation_id

        if files:
            payload["files"] = files

        try:
            logger.info(f"调用 Dify Chat API: {url}, user={user_id}")
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Dify Chat API 调用成功")
            return result

        except httpx.HTTPStatusError as e:
            logger.error(f"Dify API HTTP 错误: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Dify API 调用失败: {e}", exc_info=True)
            raise

    async def chat_stream(
        self,
        query: str,
        user_id: str,
        conversation_id: Optional[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
        files: Optional[list] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        调用 Dify Chat API (流式模式)

        Args:
            query: 用户查询
            user_id: 用户 ID
            conversation_id: 会话 ID (可选)
            inputs: 额外输入参数
            files: 文件列表 (可选)

        Yields:
            流式响应数据块
        """
        client = await self._get_client()
        url = f"{self.base_url}/chat-messages"

        payload = {
            "query": query,
            "user": user_id,
            "response_mode": "streaming",
            "inputs": inputs if inputs is not None else {},  # inputs 是必需参数
        }

        if conversation_id:
            payload["conversation_id"] = conversation_id

        if files:
            payload["files"] = files

        try:
            logger.info(f"调用 Dify Chat API (流式): {url}, user={user_id}")
            async with client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # 移除 "data: " 前缀
                        if data.strip():
                            import json
                            try:
                                yield json.loads(data)
                            except json.JSONDecodeError:
                                logger.warning(f"无法解析 SSE 数据: {data}")
                                continue

        except httpx.HTTPStatusError as e:
            logger.error(f"Dify API HTTP 错误: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Dify API 流式调用失败: {e}", exc_info=True)
            raise

    async def run_workflow(
        self,
        inputs: Dict[str, Any],
        user_id: str,
        response_mode: str = "blocking",
        files: Optional[list] = None,
    ) -> Dict[str, Any]:
        """
        调用 Dify Workflow API

        Args:
            inputs: 工作流输入参数
            user_id: 用户 ID
            response_mode: 响应模式 ('blocking' 或 'streaming')
            files: 文件列表 (可选)

        Returns:
            API 响应结果
        """
        client = await self._get_client()
        url = f"{self.base_url}/workflows/run"

        payload = {
            "inputs": inputs,
            "user": user_id,
            "response_mode": response_mode,
        }

        if files:
            payload["files"] = files

        try:
            logger.info(f"调用 Dify Workflow API: {url}, user={user_id}")
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Dify Workflow API 调用成功")
            return result

        except httpx.HTTPStatusError as e:
            logger.error(f"Dify Workflow API HTTP 错误: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Dify Workflow API 调用失败: {e}", exc_info=True)
            raise

    async def get_conversation_messages(
        self,
        conversation_id: str,
        user_id: str,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        获取会话历史消息

        Args:
            conversation_id: 会话 ID
            user_id: 用户 ID
            limit: 消息数量限制

        Returns:
            消息列表
        """
        client = await self._get_client()
        url = f"{self.base_url}/messages"

        params = {
            "conversation_id": conversation_id,
            "user": user_id,
            "limit": limit,
        }

        try:
            logger.info(f"获取 Dify 会话消息: conversation_id={conversation_id}")
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"获取会话消息失败: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"获取会话消息失败: {e}", exc_info=True)
            raise

    async def stop_message(
        self,
        task_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        停止消息生成

        Args:
            task_id: 任务 ID
            user_id: 用户 ID

        Returns:
            停止结果
        """
        client = await self._get_client()
        url = f"{self.base_url}/chat-messages/{task_id}/stop"

        payload = {"user": user_id}

        try:
            logger.info(f"停止 Dify 消息生成: task_id={task_id}")
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"停止消息失败: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"停止消息失败: {e}", exc_info=True)
            raise

    def __del__(self):
        """析构函数,确保客户端关闭"""
        if self._client and not self._client.is_closed:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.close())
                else:
                    loop.run_until_complete(self.close())
            except Exception:
                pass

