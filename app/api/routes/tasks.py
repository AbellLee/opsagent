from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
from uuid import UUID
from app.core.logger import logger
import json
import asyncio
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

# 存储WebSocket连接
websocket_connections: Dict[str, List[WebSocket]] = {}

# 导出 websocket_connections 供其他模块使用
__all__ = ["router", "notify_task_update", "websocket_connections"]

async def notify_task_update(session_id: str):
    """通知指定会话的任务更新"""
    session_id_str = str(session_id)
    logger.info(f"准备通知任务更新: session_id={session_id_str}")
    
    if session_id_str in websocket_connections:
        # 向所有WebSocket连接发送更新消息
        disconnected_connections = []
        for websocket in websocket_connections[session_id_str]:
            try:
                await websocket.send_text(json.dumps({
                    "type": "task_update", 
                    "session_id": session_id_str
                }))
            except WebSocketDisconnect:
                disconnected_connections.append(websocket)
            except Exception as e:
                logger.error(f"向WebSocket发送消息失败: {e}", exc_info=True)
                disconnected_connections.append(websocket)
        
        # 清理断开的连接
        for websocket in disconnected_connections:
            if websocket in websocket_connections[session_id_str]:
                websocket_connections[session_id_str].remove(websocket)
        
        logger.info(f"已向 {len(websocket_connections[session_id_str])} 个客户端发送任务更新通知")
    else:
        logger.info(f"会话 {session_id_str} 没有活跃的WebSocket连接")

@router.websocket("/ws/{session_id}")
async def websocket_tasks(websocket: WebSocket, session_id: UUID):
    """任务WebSocket端点"""
    session_id_str = str(session_id)
    
    # 接受WebSocket连接
    await websocket.accept()
    
    # 将连接添加到会话连接列表中
    if session_id_str not in websocket_connections:
        websocket_connections[session_id_str] = []
    
    websocket_connections[session_id_str].append(websocket)
    logger.info(f"任务WebSocket连接已建立: session_id={session_id_str}, 当前连接数={len(websocket_connections[session_id_str])}")
    
    try:
        # 发送初始连接确认消息
        await websocket.send_text(json.dumps({
            "type": "connected", 
            "session_id": session_id_str
        }))
        
        # 保持连接并监听客户端消息
        while True:
            # 等待接收消息，设置60秒超时
            data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
            try:
                message = json.loads(data)
                # 处理心跳消息
                if message.get("type") == "heartbeat":
                    # 回复心跳
                    await websocket.send_text(json.dumps({
                        "type": "heartbeat_ack"
                    }))
                # 处理用户确认响应
                elif message.get("type") == "user_confirmation_response":
                    confirmation_id = message.get("confirmation_id")
                    if confirmation_id:
                        # 延迟导入以避免循环导入
                        from app.agent.tools.custom_tools import resolve_user_confirmation
                        
                        # 解决用户确认请求
                        resolve_user_confirmation(confirmation_id, message)
                        logger.info(f"已处理用户确认响应: confirmation_id={confirmation_id}")
                # 可以在这里处理其他类型的消息
            except json.JSONDecodeError:
                logger.warning(f"收到无效的JSON消息: {data}")
    except WebSocketDisconnect:
        logger.info(f"任务WebSocket连接断开: session_id={session_id_str}")
    except Exception as e:
        logger.error(f"任务WebSocket连接异常: session_id={session_id_str}, error={e}")
    finally:
        # 清理连接
        if session_id_str in websocket_connections and websocket in websocket_connections[session_id_str]:
            websocket_connections[session_id_str].remove(websocket)
            logger.info(f"WebSocket连接已关闭: session_id={session_id_str}, 剩余连接数={len(websocket_connections.get(session_id_str, []))}")
            # 如果没有客户端连接了，清理该会话的条目
            if not websocket_connections[session_id_str]:
                del websocket_connections[session_id_str]

# 导出通知函数供其他模块使用
__all__ = ["router", "notify_task_update"]