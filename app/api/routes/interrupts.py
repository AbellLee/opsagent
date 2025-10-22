"""
中断API路由模块
负责处理与中断对话相关的HTTP请求
"""
from fastapi import APIRouter, HTTPException, status, Depends
from uuid import UUID
from pydantic import BaseModel
from app.core.logger import logger
from app.api.deps import get_db
from app.services.agent.interrupt_service import get_interrupt_service

# 创建路由器
router = APIRouter(prefix="/api/sessions", tags=["interrupts"])


class InterruptRequest(BaseModel):
    """中断请求模型"""
    reason: str = "User requested interrupt"


@router.post("/{session_id}/interrupt", status_code=status.HTTP_204_NO_CONTENT)
async def interrupt_session(
    session_id: UUID,
    request: InterruptRequest,
    db = Depends(get_db)
):
    """
    中断指定会话的对话
    
    Args:
        session_id: 会话ID
        request: 中断请求参数
    """
    try:
        # 验证会话是否存在
        cursor = db.cursor()
        cursor.execute(
            "SELECT session_id FROM user_sessions WHERE session_id = %s",
            (str(session_id),)
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )
        
        # 请求中断
        interrupt_service = get_interrupt_service()
        interrupt_service.request_interrupt(str(session_id), request.reason)
        
        logger.info(f"已请求中断会话: session_id={session_id}, reason={request.reason}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"中断会话失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"中断会话失败: {str(e)}"
        )