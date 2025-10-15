"""
Agent服务相关的数据模型
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal, Union


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
    response: Union[str, Dict[str, Any]]  # 支持字符串或消息对象
    status: str
    created_at: float
    model: str
    usage: Optional[Dict[str, Any]] = None
    messages: Optional[List[Dict[str, Any]]] = None  # 新增：结构化消息数据


class ChunkChatCompletionResponse(BaseModel):
    """流式模式的响应块模型"""
    session_id: str
    chunk: str
    status: str
    created_at: float
    model: str
    is_final: bool = False
    message_type: Optional[str] = "assistant"  # 消息类型：assistant, tool_call, tool_result
    tool_calls: Optional[List[Dict[str, Any]]] = None  # 工具调用信息
    tool_name: Optional[str] = None  # 工具名称（用于tool_result类型）
    tool_call_id: Optional[str] = None  # 工具调用ID（用于tool_result类型）
