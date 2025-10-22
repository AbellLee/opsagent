"""
中断服务模块，用于处理用户主动中断对话的请求
"""
import asyncio
import uuid
from typing import Dict, Any, Optional
from app.core.logger import logger

class InterruptService:
    """中断服务类"""
    
    def __init__(self):
        # 存储会话的中断事件，键为session_id，值为asyncio.Event
        self._interrupt_events: Dict[str, asyncio.Event] = {}
        # 存储会话的中断状态，键为session_id，值为中断原因
        self._interrupt_status: Dict[str, str] = {}
    
    def request_interrupt(self, session_id: str, reason: str = "User requested interrupt") -> None:
        """
        请求中断指定会话的对话
        
        Args:
            session_id: 会话ID
            reason: 中断原因
        """
        logger.info(f"收到中断请求: session_id={session_id}, reason={reason}")
        
        # 设置中断状态
        self._interrupt_status[session_id] = reason
        
        # 如果存在中断事件，则触发它
        if session_id in self._interrupt_events:
            event = self._interrupt_events[session_id]
            if not event.is_set():
                event.set()
                logger.info(f"已触发中断事件: session_id={session_id}")
    
    def register_interrupt_event(self, session_id: str) -> asyncio.Event:
        """
        为会话注册一个中断事件
        
        Args:
            session_id: 会话ID
            
        Returns:
            asyncio.Event: 中断事件
        """
        # 创建或获取中断事件
        if session_id not in self._interrupt_events:
            self._interrupt_events[session_id] = asyncio.Event()
        
        # 重置事件状态
        self._interrupt_events[session_id].clear()
        logger.info(f"已注册中断事件: session_id={session_id}")
        return self._interrupt_events[session_id]
    
    def check_interrupt_requested(self, session_id: str) -> bool:
        """
        检查是否请求了中断
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 是否请求了中断
        """
        return session_id in self._interrupt_status
    
    def get_interrupt_reason(self, session_id: str) -> Optional[str]:
        """
        获取中断原因
        
        Args:
            session_id: 会话ID
            
        Returns:
            str: 中断原因，如果没有中断则返回None
        """
        return self._interrupt_status.get(session_id)
    
    def clear_interrupt(self, session_id: str) -> None:
        """
        清除会话的中断状态
        
        Args:
            session_id: 会话ID
        """
        if session_id in self._interrupt_status:
            del self._interrupt_status[session_id]
        
        if session_id in self._interrupt_events:
            self._interrupt_events[session_id].clear()
        
        logger.info(f"已清除中断状态: session_id={session_id}")
    
    async def wait_for_interrupt(self, session_id: str, timeout: Optional[float] = None) -> bool:
        """
        等待中断事件触发
        
        Args:
            session_id: 会话ID
            timeout: 超时时间（秒），None表示无限等待
            
        Returns:
            bool: True表示中断事件被触发，False表示超时
        """
        # 注册中断事件
        event = self.register_interrupt_event(session_id)
        
        try:
            if timeout is not None:
                # 带超时等待
                await asyncio.wait_for(event.wait(), timeout=timeout)
            else:
                # 无限等待
                await event.wait()
            return True
        except asyncio.TimeoutError:
            return False

# 全局中断服务实例
interrupt_service = InterruptService()

def get_interrupt_service() -> InterruptService:
    """获取全局中断服务实例"""
    return interrupt_service