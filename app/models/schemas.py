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
    llm_config_id: Optional[UUID] = Field(None, description="LLM配置ID，为空时使用默认配置")

class Session(BaseModel):
    session_id: UUID
    user_id: UUID
    session_name: str = "新建对话"
    llm_config_id: Optional[UUID] = None
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
    files: Optional[List[Dict[str, Any]]] = Field(None, description="上传的文件列表，支持图片等多模态内容")


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


# Dify API 兼容模型
class DifyChatRequest(BaseModel):
    """Dify聊天请求模型"""
    inputs: Optional[Dict[str, Any]] = Field(default_factory=dict, description="输入变量")
    query: str = Field(..., description="用户输入的消息内容")
    response_mode: str = Field(
        default="blocking",
        description="响应模式：blocking为阻塞模式，streaming为流式模式"
    )
    conversation_id: Optional[str] = Field(None, description="会话ID，为空时创建新会话")
    user: str = Field(..., description="用户标识")
    files: Optional[List[Dict[str, Any]]] = Field(None, description="上传的文件列表")
    model_config_id: Optional[str] = Field(None, description="LLM配置ID，为空时使用默认配置")


class DifyChatResponse(BaseModel):
    """Dify聊天响应模型（阻塞模式）"""
    event: str = Field(default="message", description="事件类型")
    message_id: str = Field(..., description="消息ID")
    conversation_id: str = Field(..., description="会话ID")
    mode: str = Field(default="chat", description="应用模式")
    answer: str = Field(..., description="AI回复内容")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    created_at: int = Field(..., description="创建时间戳")


class DifyStreamResponse(BaseModel):
    """Dify流式响应模型"""
    event: str = Field(..., description="事件类型：message, agent_message, agent_thought, message_end等")
    task_id: Optional[str] = Field(None, description="任务ID")
    message_id: Optional[str] = Field(None, description="消息ID")
    conversation_id: str = Field(..., description="会话ID")
    answer: Optional[str] = Field(None, description="回复内容片段")
    created_at: Optional[int] = Field(None, description="创建时间戳")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
