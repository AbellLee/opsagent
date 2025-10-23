from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

# 用户相关模型
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    password: str = Field(..., min_length=6, max_length=100)
    
class User(BaseModel):
    user_id: UUID
    username: str
    email: str
    created_at: datetime
    updated_at: datetime

# 会话相关模型
class SessionCreate(BaseModel):
    user_id: UUID

class Session(BaseModel):
    session_id: UUID
    user_id: UUID
    session_name: str = "新建对话"
    created_at: datetime
    expires_at: datetime

# 工具相关模型
class Tool(BaseModel):
    tool_id: UUID
    name: str
    description: Optional[str] = None
    type: str  # MCP or Custom

class ToolApprovalConfig(BaseModel):
    id: UUID
    user_id: Optional[UUID] = None  # NULL表示默认配置
    tool_id: UUID
    tool_name: str
    auto_execute: bool = False
    approval_required: bool = True
    created_at: datetime
    updated_at: datetime

# Agent相关模型
class AgentExecuteRequest(BaseModel):
    """Agent执行请求模型"""
    message: str
    tools: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None


class AgentChatRequest(BaseModel):
    """Agent聊天请求模型"""
    message: str
    response_mode: str = Field(
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
    message_type: Optional[str] = "assistant"  # 消息类型：assistant, tool_call, tool_result
    tool_calls: Optional[List[Dict[str, Any]]] = None  # 工具调用信息
    tool_name: Optional[str] = None  # 工具名称（用于tool_result类型）
    tool_call_id: Optional[str] = None  # 工具调用ID（用于tool_result类型）

# MCP服务器配置相关模型
class MCPServerConfigCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="MCP服务器名称")
    description: Optional[str] = Field(None, description="MCP服务器描述")
    config: Dict[str, Any] = Field(..., description="MCP服务器配置JSON")
    enabled: bool = Field(default=True, description="是否启用")

class MCPServerConfigUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None

class MCPServerConfig(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    config: Dict[str, Any]
    enabled: bool
    created_at: datetime
    updated_at: datetime

# MCP配置验证模型
class MCPStdioConfig(BaseModel):
    command: str = Field(..., description="执行命令")
    args: List[str] = Field(..., description="命令参数")
    transport: str = Field("stdio", description="传输协议")

class MCPHttpConfig(BaseModel):
    url: str = Field(..., description="HTTP服务器URL")
    transport: str = Field("streamable_http", description="传输协议")
