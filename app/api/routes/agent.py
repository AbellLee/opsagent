from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage

from app.core.logger import logger

from typing import Dict, Any
from langchain_core.messages import ToolMessage, AIMessage
from app.agent.graph import graph_builder
from app.core.graph_deps import app_store, app_checkpointer
from app.core.logger import logger

router = APIRouter(prefix="/api/sessions/{session_id}", tags=["agent"])

def get_session_messages_from_db(db, session_id: UUID) -> List:
    """从数据库获取会话历史消息"""
    try:
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT role, content, created_at 
            FROM session_messages 
            WHERE session_id = %s 
            ORDER BY created_at ASC
            """,
            (str(session_id),)
        )
        rows = cursor.fetchall()
        
        messages = []
        for row in rows:
            role, content, created_at = row
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
            elif role == "system":
                messages.append(SystemMessage(content=content))
            elif role == "tool":
                messages.append(ToolMessage(content=content, tool_call_id=""))
                
        logger.info(f"从数据库加载了 {len(messages)} 条历史消息")
        return messages
    except Exception as e:
        logger.error(f"获取会话历史消息失败: {e}")
        return []

def save_message_to_db(db, session_id: UUID, role: str, content: str):
    """保存消息到数据库"""
    try:
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO session_messages (session_id, role, content, created_at)
            VALUES (%s, %s, %s, %s)
            """,
            (str(session_id), role, content, datetime.now())
        )
        db.commit()
        logger.info(f"消息已保存到数据库: {role} - {content[:50]}...")
    except Exception as e:
        logger.error(f"保存消息到数据库失败: {e}")
        db.rollback()

class AgentExecuteRequest(BaseModel):
    message: str
    tools: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None

@router.post("/execute")
async def execute_agent(
    session_id: UUID,
    request: AgentExecuteRequest,
):
    """执行Agent任务"""
    try:
        # 构造输入
        inputs = {
            "messages": [
                HumanMessage(content=request.message)
            ],
            "user_id": "default_user",  # 实际应用中应从认证信息获取
            "session_id": str(session_id),
            "tool_approval_required": False,
            "pending_tool_approvals": [],
            "intermediate_steps": []
        }
        
        # 执行Agent图
        result = agent_graph.invoke(inputs)
        
        # 提取响应消息
        messages = result.get("messages", [])
        if messages:
            last_message = messages[-1]
            return {
                "session_id": session_id,
                "response": last_message.content if hasattr(last_message, 'content') else str(last_message),
                "status": "success"
            }
        else:
            return {
                "session_id": session_id,
                "response": "No response generated",
                "status": "success"
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"执行Agent任务失败: {str(e)}"
        )

@router.post("/chat")
async def chat_with_agent(
    session_id: UUID,
    request: AgentExecuteRequest,
):
    """与Agent聊天（支持连续对话）"""
    try:

        graph = graph_builder.compile(
            checkpointer=app_checkpointer,
            store=app_store,
        )
        # 检查消息是否为空
        if not request.message or not request.message.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="消息内容不能为空"
            )
        
        # 构造输入
        inputs = {
            "messages": [
                HumanMessage(content=request.message.strip())
            ],
            "user_id": "default_user",  # 实际应用中应从认证信息获取
            "session_id": str(session_id),
            "tool_approval_required": False,
            "pending_tool_approvals": [],
            "intermediate_steps": []
        }
        
        # 使用session_id作为thread_id，实现会话级别的记忆
        config = {
            "configurable": {
                "thread_id": str(session_id)
            }
        }
        
        # 执行Agent图
        result = graph.invoke(inputs, config)
        logger.info(f"Agent图执行结果: {result}")
        
        # 提取响应消息
        messages = result.get("messages", [])
        if messages:
            last_message = messages[-1]
            response_content = last_message.content if hasattr(last_message, 'content') else str(last_message)
            return {
                "session_id": session_id,
                "response": response_content,
                "status": "success"
            }
        else:
            return {
                "session_id": session_id,
                "response": "抱歉，我没有理解你的意思。",
                "status": "success"
            }
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"与Agent聊天失败: {str(e)}")
        # 检查是否是数据库连接错误
        error_detail = str(e)
        if "数据库连接失败" in error_detail or "connection to server" in error_detail:
            error_detail = "数据库连接失败，请检查数据库服务是否运行正常"
        # 如果是模型API密钥问题，提供更明确的错误信息
        elif "api key" in error_detail.lower() or "dashscope" in error_detail.lower():
            error_detail = "模型服务未配置：请配置通义千问API密钥(DASHSCOPE_API_KEY)才能使用AI功能"
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"与Agent聊天失败: {error_detail}"
        )