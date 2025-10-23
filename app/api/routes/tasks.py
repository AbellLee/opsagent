from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
from uuid import UUID
from app.core.logger import logger
import json
import asyncio
from fastapi.responses import StreamingResponse
from datetime import datetime

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

# 存储WebSocket连接
# 修改为每个会话只保持一个WebSocket连接
websocket_connections: Dict[str, WebSocket] = {}

# 存储连接状态信息
connection_status: Dict[str, dict] = {}

# 导出 websocket_connections 供其他模块使用
__all__ = ["router", "notify_task_update", "websocket_connections", "connection_status"]

async def notify_task_update(session_id: str):
    """通知指定会话的任务更新"""
    session_id_str = str(session_id)
    logger.info(f"准备通知任务更新: session_id={session_id_str}")
    
    if session_id_str in websocket_connections:
        # 更新连接状态
        if session_id_str in connection_status:
            connection_status[session_id_str]["last_activity"] = datetime.now().isoformat()
        
        # 向WebSocket连接发送更新消息
        try:
            await websocket_connections[session_id_str].send_text(json.dumps({
                "type": "task_update", 
                "session_id": session_id_str
            }))
            logger.info(f"已向会话 {session_id_str} 发送任务更新通知")
        except WebSocketDisconnect:
            # 连接已断开，清理连接
            del websocket_connections[session_id_str]
            if session_id_str in connection_status:
                connection_status[session_id_str]["state"] = "disconnected"
                connection_status[session_id_str]["disconnected_at"] = datetime.now().isoformat()
            logger.info(f"WebSocket连接已断开并清理: session_id={session_id_str}")
        except Exception as e:
            logger.error(f"向WebSocket发送消息失败: {e}", exc_info=True)
    else:
        logger.info(f"会话 {session_id_str} 没有活跃的WebSocket连接")

@router.websocket("/ws/{session_id}")
async def websocket_tasks(websocket: WebSocket, session_id: UUID):
    """任务WebSocket端点"""
    session_id_str = str(session_id)
    
    # 如果会话已有连接，先关闭旧连接
    if session_id_str in websocket_connections:
        try:
            await websocket_connections[session_id_str].close()
            del websocket_connections[session_id_str]
            logger.info(f"已关闭会话 {session_id_str} 的旧WebSocket连接")
        except Exception as e:
            logger.error(f"关闭旧WebSocket连接失败: {e}", exc_info=True)
    
    # 接受WebSocket连接
    await websocket.accept()
    
    # 将连接存储到会话中（每个会话只保持一个连接）
    websocket_connections[session_id_str] = websocket
    connection_status[session_id_str] = {
        "connected_at": datetime.now().isoformat(),
        "client": websocket.client,
        "state": "connected"
    }
    logger.info(f"任务WebSocket连接已建立: session_id={session_id_str}")
    
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
        if session_id_str in websocket_connections and websocket_connections[session_id_str] == websocket:
            del websocket_connections[session_id_str]
            if session_id_str in connection_status:
                connection_status[session_id_str]["state"] = "disconnected"
                connection_status[session_id_str]["disconnected_at"] = datetime.now().isoformat()
            logger.info(f"WebSocket连接已关闭: session_id={session_id_str}")

# 导出通知函数供其他模块使用
__all__ = ["router", "notify_task_update"]