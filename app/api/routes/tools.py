from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID, uuid4
from datetime import datetime
from app.models.schemas import Tool, ToolApprovalConfig
from app.api.deps import get_db
from app.agent.tools import tool_manager

router = APIRouter(prefix="/api/tools", tags=["tools"])

@router.get("/", response_model=List[Tool])
def list_tools(db = Depends(get_db)):
    """列出所有可用工具"""
    try:
        tools = tool_manager.list_tools()
        return tools
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取工具列表失败: {str(e)}"
        )

@router.get("/{tool_id}", response_model=Tool)
def get_tool(tool_id: UUID, db = Depends(get_db)):
    """获取特定工具详情"""
    # 这里应该从数据库或MCP注册中心获取工具详情
    # 目前抛出404作为占位符
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="工具未找到"
    )

@router.put("/{tool_id}/approval", response_model=ToolApprovalConfig)
def set_tool_approval_config(
    tool_id: UUID, 
    approval_config: ToolApprovalConfig,
    db = Depends(get_db)
):
    """设置工具审批配置"""
    try:
        # 检查工具是否存在
        # 目前跳过检查直接创建配置
        
        config_id = uuid4()
        created_at = datetime.now()
        updated_at = datetime.now()
        
        # 插入或更新数据库
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO tool_approval_config 
            (id, user_id, tool_id, tool_name, auto_execute, approval_required, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id, tool_id) 
            DO UPDATE SET 
                tool_name = EXCLUDED.tool_name,
                auto_execute = EXCLUDED.auto_execute,
                approval_required = EXCLUDED.approval_required,
                updated_at = EXCLUDED.updated_at
            """,
            (
                str(config_id),
                str(approval_config.user_id) if approval_config.user_id else None,
                str(tool_id),
                approval_config.tool_name,
                approval_config.auto_execute,
                approval_config.approval_required,
                created_at,
                updated_at
            )
        )
        db.commit()
        
        return ToolApprovalConfig(
            id=config_id,
            user_id=approval_config.user_id,
            tool_id=tool_id,
            tool_name=approval_config.tool_name,
            auto_execute=approval_config.auto_execute,
            approval_required=approval_config.approval_required,
            created_at=created_at,
            updated_at=updated_at
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"设置工具审批配置失败: {str(e)}"
        )

@router.get("/pending-approvals")
def get_pending_approvals(db = Depends(get_db)):
    """获取待审批工具列表"""
    # 这里应该查询数据库获取待审批的工具列表
    # 目前返回空列表作为占位符
    return []

@router.post("/approvals/{approval_id}/approve")
def approve_tool_execution_approval(approval_id: UUID, db = Depends(get_db)):
    """批准工具执行"""
    # 这里应该更新审批状态为已批准
    # 目前返回成功消息作为占位符
    return {"message": "工具执行已批准", "approval_id": str(approval_id)}

@router.post("/approvals/{approval_id}/reject")
def reject_tool_execution_approval(approval_id: UUID, db = Depends(get_db)):
    """拒绝工具执行"""
    # 这里应该更新审批状态为已拒绝
    # 目前返回成功消息作为占位符
    return {"message": "工具执行已拒绝", "approval_id": str(approval_id)}