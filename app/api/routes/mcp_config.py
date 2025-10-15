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
from app.services.mcp import mcp_config_service
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
    """
    验证MCP配置格式（宽松验证）

    只验证基本结构，不限制具体的传输协议类型
    支持 transport 或 type 字段来指定协议类型
    """
    if not isinstance(config, dict):
        raise ValueError("配置必须是JSON对象")

    # 支持 transport 或 type 字段
    protocol_type = config.get("transport") or config.get("type")
    if not protocol_type:
        raise ValueError("配置中必须包含 'transport' 或 'type' 字段来指定协议类型")

    # 根据协议类型进行基本验证
    if protocol_type == "stdio":
        # stdio协议需要command和args
        if not config.get("command"):
            raise ValueError("stdio协议需要 'command' 字段")
        if not config.get("args"):
            raise ValueError("stdio协议需要 'args' 字段")
        if not isinstance(config.get("args"), list):
            raise ValueError("stdio协议的 'args' 字段必须是数组")

    elif protocol_type in ["streamable_http", "http", "sse", "websocket"]:
        # 基于URL的协议需要url字段
        if not config.get("url"):
            raise ValueError(f"{protocol_type}协议需要 'url' 字段")

    # 对于其他协议类型，只记录日志，不阻止创建
    else:
        logger.info(f"检测到自定义协议类型: {protocol_type}，跳过详细验证")


@router.post("/reload")
async def reload_mcp_tools(db = Depends(get_db)):
    """重新加载MCP工具（热重载，无需重启应用）"""
    try:
        from app.agent.tools import mcp_manager

        logger.info("收到MCP工具重载请求")
        result = await mcp_manager.reload_mcp_tools()

        if result["success"]:
            logger.info(f"MCP工具重载成功: {result}")
            return result
        else:
            logger.error(f"MCP工具重载失败: {result}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重新加载MCP工具失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重新加载MCP工具失败: {str(e)}"
        )
