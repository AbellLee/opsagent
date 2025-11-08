"""LLM 配置数据库模型"""
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, TIMESTAMP, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from .base import Base


class LLMConfig(Base):
    """LLM 配置表"""
    __tablename__ = "llm_configs"
    
    # 主键
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 基本信息
    name = Column(String(100), nullable=False, unique=True, comment="配置名称")
    provider = Column(String(50), nullable=False, comment="服务商")
    model_name = Column(String(100), nullable=False, comment="模型名称")
    api_key = Column(String(500), nullable=True, comment="API密钥（加密存储）")
    base_url = Column(String(200), nullable=True, comment="API基础URL")
    
    # 模型参数
    max_tokens = Column(Integer, default=2048, nullable=False)
    temperature = Column(Float, default=0.7, nullable=False)
    top_p = Column(Float, default=1.0, nullable=False)
    frequency_penalty = Column(Float, default=0.0, nullable=False)
    presence_penalty = Column(Float, default=0.0, nullable=False)
    
    # 配置信息
    description = Column(Text, nullable=True, comment="配置描述")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")
    is_default = Column(Boolean, default=False, nullable=False, comment="是否为默认配置")
    is_embedding = Column(Boolean, default=False, nullable=False, comment="是否为嵌入模型")
    
    # 扩展配置
    extra_config = Column(JSONB, nullable=True, comment="额外配置参数")
    
    # 使用统计
    usage_count = Column(Integer, default=0, nullable=False, comment="使用次数")
    last_used_at = Column(TIMESTAMP(timezone=True), nullable=True, comment="最后使用时间")
    
    # 审计字段
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)
    
    # 约束
    __table_args__ = (
        CheckConstraint(
            "provider IN ('openai', 'deepseek', 'tongyi', 'ollama', 'vllm', 'doubao', 'zhipu', 'moonshot', 'baidu')",
            name="check_provider"
        ),
        Index("idx_llm_configs_provider", "provider"),
        Index("idx_llm_configs_is_active", "is_active"),
        Index("idx_llm_configs_is_default_embedding", "is_default", "is_embedding"),
    )
    
    def __repr__(self):
        return f"<LLMConfig(id={self.id}, name='{self.name}', provider='{self.provider}')>"
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """转换为字典"""
        data = {
            "id": str(self.id),
            "name": self.name,
            "provider": self.provider,
            "model_name": self.model_name,
            "base_url": self.base_url,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "description": self.description,
            "is_active": self.is_active,
            "is_default": self.is_default,
            "is_embedding": self.is_embedding,
            "extra_config": self.extra_config,
            "usage_count": self.usage_count,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_sensitive and self.api_key:
            data["api_key"] = self.api_key
        elif self.api_key:
            # 脱敏显示
            data["api_key_masked"] = self._mask_api_key(self.api_key)
        
        return data
    
    @staticmethod
    def _mask_api_key(api_key: str) -> str:
        """脱敏 API 密钥"""
        if not api_key or len(api_key) < 8:
            return "****"
        return f"{api_key[:4]}{'*' * (len(api_key) - 8)}{api_key[-4:]}"

