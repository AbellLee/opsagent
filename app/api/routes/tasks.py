from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict
import json
import asyncio
from uuid import UUID
from app.api.deps import get_db
from app.core.logger import logger

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

# 存储活跃的WebSocket连接
active_connections: Dict[str, List[WebSocket]] = {}

async def notify_task_update(session_id: str):
    """通知指定会话的任务更新"""
    logger.info(f"准备通知任务更新: session_id={session_id}, 当前连接数={len(active_connections.get(session_id, []))}")
    
    if session_id in active_connections:
        disconnected = []
        for connection in active_connections[session_id]:
            try:
                await connection.send_text(json.dumps({
                    "type": "task_update",
                    "session_id": session_id
                }))
                logger.info(f"已发送任务更新通知到连接: {connection}")
            except WebSocketDisconnect:
                disconnected.append(connection)
                logger.warning(f"WebSocket连接已断开: {connection}")
            except Exception as e:
                logger.error(f"发送WebSocket消息失败: {e}")
                disconnected.append(connection)
        
        # 移除断开的连接
        for connection in disconnected:
            if connection in active_connections[session_id]:
                active_connections[session_id].remove(connection)
        
        # 如果会话没有连接了，清理字典项
        if not active_connections[session_id]:
            del active_connections[session_id]
            logger.info(f"已清理会话 {session_id} 的连接")

@router.websocket("/ws/{session_id}")
async def websocket_tasks(websocket: WebSocket, session_id: UUID):
    """任务WebSocket端点"""
    # 接受WebSocket连接
    await websocket.accept()
    
    session_id_str = str(session_id)
    
    # 将连接添加到活跃连接列表
    if session_id_str not in active_connections:
        active_connections[session_id_str] = []
    active_connections[session_id_str].append(websocket)
    
    logger.info(f"任务WebSocket连接已建立: session_id={session_id_str}, 当前连接数={len(active_connections[session_id_str])}")
    
    try:
        while True:
            # 使用异步等待来接收消息，但不处理业务逻辑
            # 这样可以保持连接活跃，同时允许其他协程发送更新通知
            try:
                # 等待接收消息，设置超时以允许定期检查
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                # 简单回显消息，实际应用中可以处理客户端请求
                await websocket.send_text(f"Echo: {data}")
            except asyncio.TimeoutError:
                # 超时后继续循环，保持连接活跃
                continue
    except WebSocketDisconnect:
        logger.info(f"任务WebSocket连接已断开: session_id={session_id_str}")
    except Exception as e:
        logger.error(f"任务WebSocket连接异常: session_id={session_id_str}, error={e}")
    finally:
        # 清理连接
        if session_id_str in active_connections and websocket in active_connections[session_id_str]:
            active_connections[session_id_str].remove(websocket)
            if not active_connections[session_id_str]:
                del active_connections[session_id_str]
        await websocket.close()
        logger.info(f"WebSocket连接已关闭: session_id={session_id_str}")
        
# 导出通知函数供其他模块使用
__all__ = ["router", "notify_task_update"]