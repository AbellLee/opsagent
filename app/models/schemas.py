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
    message: str
    tools: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None

class AgentMessage(BaseModel):
    role: str  # user, assistant, tool
    content: str
    timestamp: datetime