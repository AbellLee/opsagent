"""
用户上下文管理模块
用于在多用户环境中管理用户身份和会话信息
"""
import contextvars
from typing import Optional, Dict, Any
from uuid import UUID
from app.core.logger import logger


# 创建上下文变量用于存储用户和会话信息
_user_id_var = contextvars.ContextVar('user_id', default=None)
_session_id_var = contextvars.ContextVar('session_id', default=None)
_user_info_var = contextvars.ContextVar('user_info', default=None)


def set_user_context(user_id: str, session_id: str, user_info: Optional[Dict[str, Any]] = None):
    """
    设置用户上下文信息
    
    Args:
        user_id: 用户ID
        session_id: 会话ID
        user_info: 用户详细信息（可选）
    """
    _user_id_var.set(user_id)
    _session_id_var.set(session_id)
    if user_info:
        _user_info_var.set(user_info)
    logger.debug(f"设置用户上下文: user_id={user_id}, session_id={session_id}")


def get_user_id() -> Optional[str]:
    """
    获取当前用户ID
    
    Returns:
        用户ID，如果未设置则返回None
    """
    return _user_id_var.get()


def get_session_id() -> Optional[str]:
    """
    获取当前会话ID
    
    Returns:
        会话ID，如果未设置则返回None
    """
    return _session_id_var.get()


def get_user_info() -> Optional[Dict[str, Any]]:
    """
    获取当前用户详细信息
    
    Returns:
        用户详细信息，如果未设置则返回None
    """
    return _user_info_var.get()


def get_current_context() -> Dict[str, Any]:
    """
    获取当前完整的用户上下文信息
    
    Returns:
        包含user_id、session_id和user_info的字典
    """
    return {
        "user_id": get_user_id(),
        "session_id": get_session_id(),
        "user_info": get_user_info()
    }


class UserContextManager:
    """
    用户上下文管理器
    用于在特定代码块中设置和恢复用户上下文
    """
    
    def __init__(self, user_id: str, session_id: str, user_info: Optional[Dict[str, Any]] = None):
        self.user_id = user_id
        self.session_id = session_id
        self.user_info = user_info
        self.token_user_id = None
        self.token_session_id = None
        self.token_user_info = None
    
    def __enter__(self):
        # 保存当前上下文
        self.token_user_id = _user_id_var.set(self.user_id)
        self.token_session_id = _session_id_var.set(self.session_id)
        if self.user_info:
            self.token_user_info = _user_info_var.set(self.user_info)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # 恢复之前的上下文
        if self.token_user_id:
            _user_id_var.reset(self.token_user_id)
        if self.token_session_id:
            _session_id_var.reset(self.token_session_id)
        if self.token_user_info:
            _user_info_var.reset(self.token_user_info)