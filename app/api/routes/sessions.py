from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from app.models.schemas import SessionCreate, Session
from app.api.deps import get_db

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

@router.post("", response_model=Session, status_code=status.HTTP_201_CREATED)
def create_session(session_create: SessionCreate, db = Depends(get_db)):
    """创建新会话"""
    try:
        session_id = uuid4()
        created_at = datetime.now()
        expires_at = created_at + timedelta(hours=24)  # 24小时后过期
        
        # 插入数据库
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO user_sessions (session_id, user_id, session_name, created_at, expires_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (str(session_id), str(session_create.user_id), "新建对话", created_at, expires_at)
        )
        db.commit()
        
        return Session(
            session_id=session_id,
            user_id=session_create.user_id,
            session_name="新建对话",
            created_at=created_at,
            expires_at=expires_at
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建会话失败: {str(e)}"
        )

@router.get("/{session_id}", response_model=Session)
def get_session(session_id: UUID, db = Depends(get_db)):
    """获取会话信息"""
    try:
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT session_id, user_id, session_name, created_at, expires_at
            FROM user_sessions
            WHERE session_id = %s
            """,
            (str(session_id),)
        )
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )
            
        return Session(
            session_id=UUID(row[0]),
            user_id=UUID(row[1]),
            session_name=row[2],
            created_at=row[3],
            expires_at=row[4]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取会话信息失败: {str(e)}"
        )

@router.put("/{session_id}/name")
def update_session_name(session_id: UUID, session_name: str, db = Depends(get_db)):
    """更新会话名称"""
    try:
        cursor = db.cursor()
        cursor.execute(
            """
            UPDATE user_sessions 
            SET session_name = %s 
            WHERE session_id = %s
            """,
            (session_name, str(session_id))
        )
        db.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )
            
        return {"message": "会话名称更新成功"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新会话名称失败: {str(e)}"
        )

@router.delete("/{session_id}")
def delete_session(session_id: UUID, db = Depends(get_db)):
    """删除会话"""
    try:
        cursor = db.cursor()
        cursor.execute(
            "DELETE FROM user_sessions WHERE session_id = %s",
            (str(session_id),)
        )
        db.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )
            
        return {"message": "会话删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除会话失败: {str(e)}"
        )

@router.get("/", response_model=List[Session])
def list_sessions(user_id: UUID = Query(...), db = Depends(get_db)):
    """列出用户的所有会话"""
    try:
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT session_id, user_id, session_name, created_at, expires_at
            FROM user_sessions
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (str(user_id),)
        )
        rows = cursor.fetchall()
        
        sessions = []
        for row in rows:
            sessions.append(Session(
                session_id=UUID(row[0]),
                user_id=UUID(row[1]),
                session_name=row[2],
                created_at=row[3],
                expires_at=row[4]
            ))
            
        return sessions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取会话列表失败: {str(e)}"
        )