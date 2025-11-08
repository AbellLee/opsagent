"""LLM 配置 Pydantic 模型"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class LLMConfigBase(BaseModel):
    """LLM配置基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="配置名称")
    provider: str = Field(..., description="服务商")
    model_name: str = Field(..., description="模型名称")
    api_key: Optional[str] = Field(None, description="API密钥")
    base_url: Optional[str] = Field(None, description="API基础URL")
    max_tokens: int = Field(default=2048, ge=1, le=32000, description="最大token数")
    temperature: float = Field(default=0.7, ge=0, le=2, description="温度参数")
    top_p: float = Field(default=1.0, ge=0, le=1, description="Top-p参数")
    frequency_penalty: float = Field(default=0.0, ge=-2, le=2, description="频率惩罚")
    presence_penalty: float = Field(default=0.0, ge=-2, le=2, description="存在惩罚")
    description: Optional[str] = Field(None, description="配置描述")
    is_active: bool = Field(default=True, description="是否启用")
    is_default: bool = Field(default=False, description="是否为默认配置")
    is_embedding: bool = Field(default=False, description="是否为嵌入模型")
    extra_config: Optional[Dict[str, Any]] = Field(None, description="额外配置")

    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v):
        """验证服务商"""
        allowed_providers = ['openai', 'deepseek', 'tongyi', 'ollama', 'vllm', 'doubao', 'zhipu', 'moonshot', 'baidu']
        if v not in allowed_providers:
            raise ValueError(f'provider must be one of {allowed_providers}')
        return v

    @field_validator('base_url')
    @classmethod
    def validate_url(cls, v):
        """验证 URL 格式"""
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('base_url must start with http:// or https://')
        return v


class LLMConfigCreate(LLMConfigBase):
    """创建LLM配置"""
    pass


class LLMConfigUpdate(BaseModel):
    """更新LLM配置"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    provider: Optional[str] = None
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: Optional[int] = Field(None, ge=1, le=32000)
    temperature: Optional[float] = Field(None, ge=0, le=2)
    top_p: Optional[float] = Field(None, ge=0, le=1)
    frequency_penalty: Optional[float] = Field(None, ge=-2, le=2)
    presence_penalty: Optional[float] = Field(None, ge=-2, le=2)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    is_embedding: Optional[bool] = None
    extra_config: Optional[Dict[str, Any]] = None

    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v):
        """验证服务商"""
        if v is not None:
            allowed_providers = ['openai', 'deepseek', 'tongyi', 'ollama', 'vllm', 'doubao', 'zhipu', 'moonshot', 'baidu']
            if v not in allowed_providers:
                raise ValueError(f'provider must be one of {allowed_providers}')
        return v

    @field_validator('base_url')
    @classmethod
    def validate_url(cls, v):
        """验证 URL 格式"""
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('base_url must start with http:// or https://')
        return v


class LLMConfigResponse(LLMConfigBase):
    """LLM配置响应"""
    id: UUID
    usage_count: int
    last_used_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    api_key_masked: Optional[str] = None  # 脱敏后的API密钥

    model_config = {"from_attributes": True}


class LLMConfigTest(BaseModel):
    """测试LLM配置"""
    message: Optional[str] = Field(default="Hello, this is a test message.", description="测试消息")

