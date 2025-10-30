"""Dify Agent 配置管理 API 路由"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from uuid import UUID
import time

from app.models.schemas import (
    DifyAgentCreate,
    DifyAgentUpdate,
    DifyAgentResponse,
    DifyAgentTestRequest,
    DifyAgentTestResponse,
)
from app.services.dify.manager import get_dify_manager
from app.services.dify.client import DifyClient
from app.api.deps import get_db
from app.core.logger import logger

router = APIRouter()


@router.post("/", response_model=DifyAgentResponse, status_code=status.HTTP_201_CREATED)
async def create_dify_agent(
    agent_data: DifyAgentCreate,
    db=Depends(get_db),
):
    """创建 Dify Agent 配置"""
    try:
        logger.info(f"收到创建 Dify Agent 请求: name={agent_data.name}, type={agent_data.agent_type}")

        manager = get_dify_manager()
        agent_id = await manager.create_agent(
            name=agent_data.name,
            description=agent_data.description,
            agent_type=agent_data.agent_type,
            dify_app_id=agent_data.dify_app_id,
            api_key=agent_data.api_key,
            base_url=agent_data.base_url,
            capabilities=agent_data.capabilities,
            keywords=agent_data.keywords,
            config=agent_data.config,
            priority=agent_data.priority,
        )

        # 获取创建的 Agent
        agent = await manager.get_agent_by_id(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="创建成功但无法获取 Agent 信息",
            )

        logger.info(f"创建 Dify Agent 成功: {agent.name} (ID: {agent_id})")

        return DifyAgentResponse(
            id=UUID(agent.id),
            name=agent.name,
            description=agent.description,
            agent_type=agent.agent_type,
            dify_app_id=agent.dify_app_id,
            api_key=agent.api_key,
            base_url=agent.base_url,
            capabilities=agent.capabilities,
            keywords=agent.keywords,
            config=agent.config,
            enabled=agent.enabled,
            priority=agent.priority,
            created_at=agent.created_at,
            updated_at=agent.updated_at,
        )

    except Exception as e:
        logger.error(f"创建 Dify Agent 失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建 Dify Agent 失败: {str(e)}",
        )


@router.get("/", response_model=List[DifyAgentResponse])
async def list_dify_agents(
    enabled_only: bool = False,
    db=Depends(get_db),
):
    """列出所有 Dify Agent 配置"""
    try:
        manager = get_dify_manager()
        agents = await manager.load_agents(force_reload=True)

        # 过滤
        if enabled_only:
            agents = [a for a in agents if a.enabled]

        return [
            DifyAgentResponse(
                id=UUID(agent.id),
                name=agent.name,
                description=agent.description,
                agent_type=agent.agent_type,
                dify_app_id=agent.dify_app_id,
                api_key=agent.api_key,
                base_url=agent.base_url,
                capabilities=agent.capabilities,
                keywords=agent.keywords,
                config=agent.config,
                enabled=agent.enabled,
                priority=agent.priority,
                created_at=agent.created_at,
                updated_at=agent.updated_at,
            )
            for agent in agents
        ]

    except Exception as e:
        logger.error(f"获取 Dify Agent 列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取 Dify Agent 列表失败: {str(e)}",
        )


@router.get("/{agent_id}", response_model=DifyAgentResponse)
async def get_dify_agent(
    agent_id: UUID,
    db=Depends(get_db),
):
    """获取指定的 Dify Agent 配置"""
    try:
        manager = get_dify_manager()
        agent = await manager.get_agent_by_id(str(agent_id))

        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dify Agent 不存在: {agent_id}",
            )

        return DifyAgentResponse(
            id=UUID(agent.id),
            name=agent.name,
            description=agent.description,
            agent_type=agent.agent_type,
            dify_app_id=agent.dify_app_id,
            api_key=agent.api_key,
            base_url=agent.base_url,
            capabilities=agent.capabilities,
            keywords=agent.keywords,
            config=agent.config,
            enabled=agent.enabled,
            priority=agent.priority,
            created_at=agent.created_at,
            updated_at=agent.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取 Dify Agent 失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取 Dify Agent 失败: {str(e)}",
        )


@router.put("/{agent_id}", response_model=DifyAgentResponse)
async def update_dify_agent(
    agent_id: UUID,
    agent_data: DifyAgentUpdate,
    db=Depends(get_db),
):
    """更新 Dify Agent 配置"""
    try:
        logger.info(f"收到更新 Dify Agent 请求: agent_id={agent_id}")

        manager = get_dify_manager()

        # 构建更新字段
        update_fields = agent_data.model_dump(exclude_unset=True)
        if not update_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="没有需要更新的字段",
            )

        # 执行更新
        success = await manager.update_agent(str(agent_id), **update_fields)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dify Agent 不存在: {agent_id}",
            )

        # 获取更新后的 Agent
        agent = await manager.get_agent_by_id(str(agent_id))
        logger.info(f"更新 Dify Agent 成功: {agent.name}")

        return DifyAgentResponse(
            id=UUID(agent.id),
            name=agent.name,
            description=agent.description,
            agent_type=agent.agent_type,
            dify_app_id=agent.dify_app_id,
            api_key=agent.api_key,
            base_url=agent.base_url,
            capabilities=agent.capabilities,
            keywords=agent.keywords,
            config=agent.config,
            enabled=agent.enabled,
            priority=agent.priority,
            created_at=agent.created_at,
            updated_at=agent.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新 Dify Agent 失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新 Dify Agent 失败: {str(e)}",
        )


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dify_agent(
    agent_id: UUID,
    db=Depends(get_db),
):
    """删除 Dify Agent 配置 (软删除 - 设置为禁用)"""
    try:
        logger.info(f"收到删除 Dify Agent 请求: agent_id={agent_id}")

        manager = get_dify_manager()

        # 软删除 - 设置为禁用
        success = await manager.update_agent(str(agent_id), enabled=False)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dify Agent 不存在: {agent_id}",
            )

        logger.info(f"删除 Dify Agent 成功: {agent_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除 Dify Agent 失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除 Dify Agent 失败: {str(e)}",
        )


@router.post("/{agent_id}/test", response_model=DifyAgentTestResponse)
async def test_dify_agent(
    agent_id: UUID,
    test_data: DifyAgentTestRequest,
    db=Depends(get_db),
):
    """测试 Dify Agent 连接"""
    try:
        logger.info(f"测试 Dify Agent: agent_id={agent_id}, query={test_data.query[:50]}...")

        manager = get_dify_manager()
        agent = await manager.get_agent_by_id(str(agent_id))

        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dify Agent 不存在: {agent_id}",
            )

        # 创建客户端并测试
        client = DifyClient(
            base_url=agent.base_url,
            api_key=agent.api_key,
            timeout=agent.config.get("timeout", 60),
        )

        start_time = time.time()

        try:
            if agent.agent_type == "workflow":
                inputs = agent.config.get("inputs", {})
                inputs["query"] = test_data.query
                result = await client.run_workflow(
                    inputs=inputs,
                    user_id=test_data.user_id,
                    response_mode="blocking",
                )
                response_text = str(result.get("data", {}).get("outputs", result))
            else:
                result = await client.chat(
                    query=test_data.query,
                    user_id=test_data.user_id,
                    response_mode="blocking",
                )
                response_text = result.get("answer", str(result))

            latency_ms = (time.time() - start_time) * 1000

            logger.info(f"Dify Agent 测试成功: {agent.name}, 延迟: {latency_ms:.2f}ms")

            return DifyAgentTestResponse(
                success=True,
                response=response_text,
                latency_ms=latency_ms,
            )

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"Dify Agent 测试失败: {e}")

            return DifyAgentTestResponse(
                success=False,
                error=str(e),
                latency_ms=latency_ms,
            )

        finally:
            await client.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"测试 Dify Agent 失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"测试 Dify Agent 失败: {str(e)}",
        )


@router.post("/refresh-cache", status_code=status.HTTP_200_OK)
async def refresh_agent_cache(db=Depends(get_db)):
    """手动刷新 Dify Agent 配置缓存"""
    try:
        logger.info("收到刷新 Dify Agent 缓存请求")
        manager = get_dify_manager()
        await manager.refresh_cache()
        agents = await manager.load_agents()
        logger.info(f"刷新缓存成功,当前有 {len(agents)} 个 Dify Agent")
        return {"message": f"缓存刷新成功,当前有 {len(agents)} 个 Dify Agent"}

    except Exception as e:
        logger.error(f"刷新缓存失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刷新缓存失败: {str(e)}",
        )

