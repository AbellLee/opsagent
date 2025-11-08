"""LLM 配置管理 API 路由"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db_sqlalchemy
from app.services.llm_service import LLMService
from app.models.pydantic_schemas.llm_config import (
    LLMConfigCreate,
    LLMConfigUpdate,
    LLMConfigResponse,
    LLMConfigTest
)
from app.core.logger import logger

router = APIRouter(prefix="/llm-configs", tags=["llm-configs"])


def get_llm_service(db: Session = Depends(get_db_sqlalchemy)) -> LLMService:
    """获取 LLM 服务实例"""
    return LLMService(db)


@router.get("/", response_model=List[LLMConfigResponse])
async def list_llm_configs(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大记录数"),
    search: Optional[str] = Query(None, description="搜索关键词（名称、模型名、描述）"),
    provider: Optional[str] = Query(None, description="服务商筛选"),
    is_active: Optional[bool] = Query(None, description="激活状态筛选"),
    is_embedding: Optional[bool] = Query(None, description="模型类型筛选"),
    llm_service: LLMService = Depends(get_llm_service)
):
    """获取 LLM 配置列表"""
    try:
        configs = llm_service.search_configs(
            search=search,
            provider=provider,
            is_active=is_active,
            is_embedding=is_embedding,
            skip=skip,
            limit=limit
        )
        
        # 转换为响应模型（脱敏 API 密钥）
        return [
            LLMConfigResponse(
                **config.to_dict(include_sensitive=False)
            )
            for config in configs
        ]
    except Exception as e:
        logger.error(f"获取 LLM 配置列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取配置列表失败"
        )


@router.get("/providers", response_model=List[str])
async def list_providers():
    """获取支持的 LLM 服务商列表"""
    return [
        "openai",
        "deepseek",
        "tongyi",
        "ollama",
        "vllm",
        "doubao",
        "zhipu",
        "moonshot",
        "baidu"
    ]


@router.get("/active", response_model=List[LLMConfigResponse])
async def list_active_configs(
    is_embedding: Optional[bool] = Query(None, description="模型类型筛选"),
    llm_service: LLMService = Depends(get_llm_service)
):
    """获取所有激活的 LLM 配置"""
    try:
        configs = llm_service.get_active_configs(is_embedding=is_embedding)
        return [
            LLMConfigResponse(**config.to_dict(include_sensitive=False))
            for config in configs
        ]
    except Exception as e:
        logger.error(f"获取激活配置列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取激活配置列表失败"
        )


@router.get("/default", response_model=LLMConfigResponse)
async def get_default_config(
    is_embedding: bool = Query(False, description="是否获取嵌入模型默认配置"),
    llm_service: LLMService = Depends(get_llm_service)
):
    """获取默认 LLM 配置"""
    try:
        config = llm_service.get_default_config(is_embedding=is_embedding)
        if not config:
            model_type = "嵌入模型" if is_embedding else "对话模型"
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到默认{model_type}配置"
            )
        return LLMConfigResponse(**config.to_dict(include_sensitive=False))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取默认配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取默认配置失败"
        )


@router.get("/{config_id}", response_model=LLMConfigResponse)
async def get_llm_config(
    config_id: UUID,
    llm_service: LLMService = Depends(get_llm_service)
):
    """获取 LLM 配置详情"""
    try:
        config = llm_service.get_config(config_id)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="配置不存在"
            )
        return LLMConfigResponse(**config.to_dict(include_sensitive=False))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取配置详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取配置详情失败"
        )


@router.post("/", response_model=LLMConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_llm_config(
    config_data: LLMConfigCreate,
    llm_service: LLMService = Depends(get_llm_service)
):
    """创建 LLM 配置"""
    try:
        config = llm_service.create_config(config_data)
        return LLMConfigResponse(**config.to_dict(include_sensitive=False))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"创建配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建配置失败"
        )


@router.put("/{config_id}", response_model=LLMConfigResponse)
async def update_llm_config(
    config_id: UUID,
    config_data: LLMConfigUpdate,
    llm_service: LLMService = Depends(get_llm_service)
):
    """更新 LLM 配置"""
    try:
        config = llm_service.update_config(config_id, config_data)
        return LLMConfigResponse(**config.to_dict(include_sensitive=False))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"更新配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新配置失败"
        )


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_llm_config(
    config_id: UUID,
    llm_service: LLMService = Depends(get_llm_service)
):
    """删除 LLM 配置"""
    try:
        llm_service.delete_config(config_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"删除配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除配置失败"
        )


@router.post("/{config_id}/toggle-status", response_model=dict)
async def toggle_config_status(
    config_id: UUID,
    llm_service: LLMService = Depends(get_llm_service)
):
    """切换配置激活状态"""
    try:
        config = llm_service.toggle_active(config_id)
        status_text = "激活" if config.is_active else "禁用"
        return {
            "message": f"配置已{status_text}",
            "is_active": config.is_active
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"切换配置状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="切换配置状态失败"
        )


@router.post("/{config_id}/set-default", response_model=dict)
async def set_default_config(
    config_id: UUID,
    llm_service: LLMService = Depends(get_llm_service)
):
    """设置为默认配置"""
    try:
        config = llm_service.set_as_default(config_id)
        model_type = "嵌入模型" if config.is_embedding else "对话模型"
        return {
            "message": f"已将 {config.name} 设为默认{model_type}配置",
            "is_default": config.is_default
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"设置默认配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="设置默认配置失败"
        )


@router.post("/{config_id}/test", response_model=dict)
async def test_llm_config(
    config_id: UUID,
    test_data: LLMConfigTest,
    llm_service: LLMService = Depends(get_llm_service)
):
    """测试 LLM 配置"""
    try:
        # 获取配置
        config = llm_service.get_config(config_id, decrypt_api_key=True)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="配置不存在"
            )
        
        # 尝试创建模型实例并测试
        test_message = test_data.message or "Hello, this is a test message."
        
        try:
            if config.is_embedding:
                # 测试嵌入模型
                embedding_model = llm_service.get_embedding_model(config_id=config_id)
                result = embedding_model.embed_query(test_message)
                return {
                    "success": True,
                    "message": "嵌入模型测试成功",
                    "test_message": test_message,
                    "embedding_dimension": len(result),
                    "config_info": config.to_dict(include_sensitive=False)
                }
            else:
                # 测试聊天模型
                chat_model = llm_service.get_chat_model(config_id=config_id)
                from langchain_core.messages import HumanMessage
                response = chat_model.invoke([HumanMessage(content=test_message)])
                return {
                    "success": True,
                    "message": "聊天模型测试成功",
                    "test_message": test_message,
                    "response": response.content,
                    "config_info": config.to_dict(include_sensitive=False)
                }
        except Exception as test_error:
            logger.error(f"LLM 配置测试失败: {test_error}")
            return {
                "success": False,
                "message": f"配置测试失败: {str(test_error)}",
                "test_message": test_message,
                "config_info": config.to_dict(include_sensitive=False)
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"测试配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="测试配置失败"
        )

