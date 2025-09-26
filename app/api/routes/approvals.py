from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel
from app.api.deps import get_db
from app.agent.tools import tool_manager
from app.core.logger import logger

router = APIRouter(prefix="/api/approvals", tags=["approvals"])

class ApprovalRequest(BaseModel):
    tool_name: str
    tool_input: Dict[str, Any]
    user_id: str
    session_id: str

class ApprovalItem(BaseModel):
    id: str
    tool_name: str
    tool_input: Dict[str, Any]
    user_id: str
    session_id: str
    created_at: datetime

# 存储待审批项的内存存储（在实际应用中应使用数据库）
pending_approvals = {}

@router.post("/")
def request_approval(request: ApprovalRequest, db = Depends(get_db)):
    """请求工具执行审批"""
    try:
        approval_id = str(uuid4())
        created_at = datetime.now()
        
        # 存储待审批项
        pending_approvals[approval_id] = {
            "id": approval_id,
            "tool_name": request.tool_name,
            "tool_input": request.tool_input,
            "user_id": request.user_id,
            "session_id": request.session_id,
            "created_at": created_at
        }
        
        return {
            "approval_id": approval_id,
            "message": "审批请求已提交",
            "created_at": created_at
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提交审批请求失败: {str(e)}"
        )

@router.get("/", response_model=List[ApprovalItem])
def list_approvals(db = Depends(get_db)):
    """列出所有待审批项"""
    try:
        return list(pending_approvals.values())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取审批列表失败: {str(e)}"
        )

@router.post("/{approval_id}/approve")
def approve_execution(approval_id: str, db = Depends(get_db)):
    """批准工具执行"""
    try:
        if approval_id not in pending_approvals:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="审批请求未找到"
            )
        
        approval_item = pending_approvals[approval_id]
        
        # 执行工具
        result = tool_manager.execute_tool(
            approval_item["tool_name"], 
            approval_item["tool_input"], 
            approval_item["user_id"]
        )
        
        # 从待审批列表中移除
        del pending_approvals[approval_id]
        
        return {
            "approval_id": approval_id,
            "result": result,
            "message": "工具执行已批准并执行"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批准工具执行失败: {str(e)}"
        )

@router.post("/{approval_id}/reject")
def reject_execution(approval_id: str, db = Depends(get_db)):
    """拒绝工具执行"""
    try:
        if approval_id not in pending_approvals:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="审批请求未找到"
            )
        
        # 从待审批列表中移除
        approval_item = pending_approvals.pop(approval_id)
        
        return {
            "approval_id": approval_id,
            "message": "工具执行已拒绝",
            "tool_name": approval_item["tool_name"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"拒绝工具执行失败: {str(e)}"
        )