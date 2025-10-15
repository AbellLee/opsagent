"""
MCP服务器配置管理API路由
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Dict, Any
from uuid import UUID

from app.models.schemas import (
    MCPServerConfig, 
    MCPServerConfigCreate, 
    MCPServerConfigUpdate,
    MCPStdioConfig,
    MCPHttpConfig
)
from app.services.mcp_config import mcp_config_service
from app.api.deps import get_db
from app.core.logger import logger

router = APIRouter()


@router.post("/", response_model=MCPServerConfig)
def create_mcp_config(
    config_data: MCPServerConfigCreate,
    db = Depends(get_db)
):
    """创建MCP服务器配置"""
    try:
        logger.info(f"收到创建MCP配置请求: name={config_data.name}, config={config_data.config}")

        # 验证配置格式
        _validate_mcp_config(config_data.config)
        logger.info("MCP配置格式验证通过")

        config = mcp_config_service.create_mcp_config(config_data)
        logger.info(f"创建MCP配置成功: {config.name}")
        return config
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"创建MCP配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建MCP配置失败: {str(e)}"
        )


@router.get("/", response_model=List[MCPServerConfig])
def list_mcp_configs(
    enabled_only: bool = False,
    db = Depends(get_db)
):
    """列出所有MCP服务器配置"""
    try:
        configs = mcp_config_service.list_mcp_configs(enabled_only=enabled_only)
        return configs
    except Exception as e:
        logger.error(f"获取MCP配置列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取MCP配置列表失败: {str(e)}"
        )


@router.get("/{config_id}", response_model=MCPServerConfig)
def get_mcp_config(
    config_id: UUID,
    db = Depends(get_db)
):
    """获取指定的MCP服务器配置"""
    try:
        config = mcp_config_service.get_mcp_config(config_id)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="MCP配置不存在"
            )
        return config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取MCP配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取MCP配置失败: {str(e)}"
        )


@router.put("/{config_id}", response_model=MCPServerConfig)
def update_mcp_config(
    config_id: UUID,
    update_data: MCPServerConfigUpdate,
    db = Depends(get_db)
):
    """更新MCP服务器配置"""
    try:
        # 如果更新配置内容，需要验证格式
        if update_data.config is not None:
            _validate_mcp_config(update_data.config)
            
        config = mcp_config_service.update_mcp_config(config_id, update_data)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="MCP配置不存在"
            )
            
        logger.info(f"更新MCP配置成功: {config.name}")
        return config
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新MCP配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新MCP配置失败: {str(e)}"
        )


@router.delete("/{config_id}")
def delete_mcp_config(
    config_id: UUID,
    db = Depends(get_db)
):
    """删除MCP服务器配置"""
    try:
        success = mcp_config_service.delete_mcp_config(config_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="MCP配置不存在"
            )
            
        logger.info(f"删除MCP配置成功: {config_id}")
        return {"message": "MCP配置删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除MCP配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除MCP配置失败: {str(e)}"
        )


@router.post("/{config_id}/toggle")
def toggle_mcp_config(
    config_id: UUID,
    db = Depends(get_db)
):
    """切换MCP服务器配置的启用状态"""
    try:
        # 获取当前配置
        current_config = mcp_config_service.get_mcp_config(config_id)
        if not current_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="MCP配置不存在"
            )
            
        # 切换启用状态
        update_data = MCPServerConfigUpdate(enabled=not current_config.enabled)
        updated_config = mcp_config_service.update_mcp_config(config_id, update_data)
        
        status_text = "启用" if updated_config.enabled else "禁用"
        logger.info(f"{status_text}MCP配置: {updated_config.name}")
        
        return {
            "message": f"MCP配置已{status_text}",
            "config": updated_config
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"切换MCP配置状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"切换MCP配置状态失败: {str(e)}"
        )


@router.get("/validate/config")
def validate_mcp_config_format(config: Dict[str, Any]):
    """验证MCP配置格式"""
    try:
        _validate_mcp_config(config)
        return {"valid": True, "message": "配置格式正确"}
    except ValueError as e:
        return {"valid": False, "message": str(e)}


def _validate_mcp_config(config: Dict[str, Any]) -> None:
    """验证MCP配置格式"""
    if not isinstance(config, dict):
        raise ValueError("配置必须是JSON对象")
        
    transport = config.get("transport")
    if not transport:
        raise ValueError("缺少transport字段")
        
    if transport == "stdio":
        try:
            MCPStdioConfig(**config)
        except Exception as e:
            raise ValueError(f"stdio配置格式错误: {e}")
            
    elif transport == "streamable_http":
        try:
            MCPHttpConfig(**config)
        except Exception as e:
            raise ValueError(f"HTTP配置格式错误: {e}")
            
    else:
        raise ValueError(f"不支持的传输协议: {transport}")


@router.post("/reload")
def reload_mcp_tools(db = Depends(get_db)):
    """重新加载MCP工具（需要重启工具管理器）"""
    try:
        # 这里可以添加重新加载MCP工具的逻辑
        # 目前需要重启应用才能生效
        return {
            "message": "MCP配置已更新，请重启应用以使新配置生效",
            "note": "未来版本将支持热重载"
        }
    except Exception as e:
        logger.error(f"重新加载MCP工具失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重新加载MCP工具失败: {str(e)}"
        )
