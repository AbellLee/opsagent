"""
Agent服务相关的数据模型
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal


class AgentExecuteRequest(BaseModel):
    """Agent执行请求模型"""
    message: str
    tools: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None


class AgentChatRequest(BaseModel):
    """Agent聊天请求模型"""
    message: str
    response_mode: Literal["blocking", "streaming"] = Field(
        default="blocking", 
        description="响应模式：blocking为阻塞模式，streaming为流式模式"
    )
    tools: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None


class ChatCompletionResponse(BaseModel):
    """阻塞模式的响应模型"""
    session_id: str
    response: str
    status: str
    created_at: float
    model: str
    usage: Optional[Dict[str, Any]] = None


class ChunkChatCompletionResponse(BaseModel):
    """流式模式的响应块模型"""
    session_id: str
    chunk: str
    status: str
    created_at: float
    model: str
    is_final: bool = False
