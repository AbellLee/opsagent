from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID, uuid4
from datetime import datetime
from app.models.schemas import UserCreate, User
from app.api.deps import get_db

router = APIRouter(prefix="/api/users", tags=["users"])

@router.post("/", response_model=User)
def create_user(user_create: UserCreate, db = Depends(get_db)):
    """用户注册"""
    try:
        # 检查用户名或邮箱是否已存在
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT user_id FROM users 
            WHERE username = %s OR email = %s
            """,
            (user_create.username, user_create.email)
        )
        
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名或邮箱已存在"
            )
        
        user_id = uuid4()
        created_at = datetime.now()
        updated_at = datetime.now()
        
        # 插入新用户
        cursor.execute(
            """
            INSERT INTO users (user_id, username, email, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (str(user_id), user_create.username, user_create.email, created_at, updated_at)
        )
        db.commit()
        
        return User(
            user_id=user_id,
            username=user_create.username,
            email=user_create.email,
            created_at=created_at,
            updated_at=updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"用户注册失败: {str(e)}"
        )

@router.post("/login")
def login_user(user_create: UserCreate, db = Depends(get_db)):
    """用户登录"""
    try:
        # 在实际应用中，这里应该验证用户名/邮箱和密码
        # 目前简化处理，只检查用户是否存在
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT user_id, username, email, created_at, updated_at FROM users 
            WHERE username = %s OR email = %s
            """,
            (user_create.username, user_create.email)
        )
        
        row = cursor.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        # 在实际应用中，这里应该生成并返回JWT token
        # 目前返回占位符token
        return {
            "user": {
                "user_id": row[0],
                "username": row[1],
                "email": row[2],
                "created_at": row[3],
                "updated_at": row[4]
            },
            "token": "placeholder_token_" + str(uuid4()),
            "message": "登录成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}"
        )

@router.get("/profile", response_model=User)
def get_user_profile(db = Depends(get_db)):
    """获取用户信息"""
    # 这里应该根据认证信息获取当前用户信息
    # 目前返回占位符数据
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="请先登录"
    )

@router.put("/profile", response_model=User)
def update_user_profile(user_update: UserCreate, db = Depends(get_db)):
    """更新用户信息"""
    # 这里应该根据认证信息更新当前用户信息
    # 目前返回401错误
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="请先登录"
    )