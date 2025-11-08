"""LLM 服务层 - 管理 LLM 配置和调用"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from langchain_openai import ChatOpenAI
from langchain_core.embeddings import Embeddings

from app.db.repositories.llm_config import LLMConfigRepository
from app.models.database.llm_config import LLMConfig
from app.models.pydantic_schemas.llm_config import LLMConfigCreate, LLMConfigUpdate
from app.core.logger import logger
from app.utils.encryption import encryption


class LLMService:
    """LLM 服务 - 提供 LLM 配置管理和模型实例化"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = LLMConfigRepository(db)
    
    # ==================== 配置管理 ====================
    
    def create_config(
        self, 
        config_data: LLMConfigCreate, 
        created_by: Optional[UUID] = None
    ) -> LLMConfig:
        """创建 LLM 配置"""
        try:
            # 检查名称是否已存在
            existing = self.repository.get_by_name(config_data.name)
            if existing:
                raise ValueError(f"配置名称 '{config_data.name}' 已存在")

            # 如果设为默认，取消同类型的其他默认配置
            if config_data.is_default:
                # 取消同类型的其他默认配置
                self.db.query(LLMConfig).filter(
                    LLMConfig.is_embedding == config_data.is_embedding
                ).update({"is_default": False})
                self.db.commit()

            # 加密 API 密钥
            encrypted_api_key = None
            if config_data.api_key:
                encrypted_api_key = encryption.encrypt(config_data.api_key)

            # 创建配置对象
            config = LLMConfig(
                name=config_data.name,
                provider=config_data.provider,
                model_name=config_data.model_name,
                api_key=encrypted_api_key,
                base_url=config_data.base_url,
                max_tokens=config_data.max_tokens,
                temperature=config_data.temperature,
                top_p=config_data.top_p,
                frequency_penalty=config_data.frequency_penalty,
                presence_penalty=config_data.presence_penalty,
                description=config_data.description,
                is_active=config_data.is_active,
                is_default=config_data.is_default,
                is_embedding=config_data.is_embedding,
                extra_config=config_data.extra_config or {},
                created_by=created_by,
                updated_by=created_by
            )

            # 添加到数据库
            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)
            created = config
            logger.info(f"创建 LLM 配置: {created.name} (ID: {created.id})")
            return created

        except Exception as e:
            logger.error(f"创建 LLM 配置失败: {e}")
            raise
    
    def update_config(
        self,
        config_id: UUID,
        config_data: LLMConfigUpdate,
        updated_by: Optional[UUID] = None
    ) -> LLMConfig:
        """更新 LLM 配置"""
        try:
            config = self.repository.get(config_id)
            if not config:
                raise ValueError(f"配置不存在: {config_id}")
            
            # 检查名称是否冲突
            if config_data.name and config_data.name != config.name:
                existing = self.repository.get_by_name(config_data.name)
                if existing:
                    raise ValueError(f"配置名称 '{config_data.name}' 已存在")
            
            # 如果设为默认，取消同类型的其他默认配置
            if config_data.is_default is True:
                is_embedding = config_data.is_embedding if config_data.is_embedding is not None else config.is_embedding
                self.repository.set_default(
                    config_id=config_id,
                    is_embedding=is_embedding,
                    set_default=True
                )
            
            # 更新字段
            update_data = config_data.dict(exclude_unset=True)
            
            # 加密 API 密钥
            if 'api_key' in update_data and update_data['api_key']:
                update_data['api_key'] = encryption.encrypt(update_data['api_key'])
            
            # 添加审计字段
            update_data['updated_by'] = updated_by
            
            updated = self.repository.update(config_id, update_data)
            logger.info(f"更新 LLM 配置: {updated.name} (ID: {updated.id})")
            return updated
            
        except Exception as e:
            logger.error(f"更新 LLM 配置失败: {e}")
            raise
    
    def delete_config(self, config_id: UUID) -> bool:
        """删除 LLM 配置"""
        try:
            config = self.repository.get(config_id)
            if not config:
                raise ValueError(f"配置不存在: {config_id}")
            
            # TODO: 检查是否有会话正在使用该配置
            # 可以添加级联删除或阻止删除的逻辑
            
            self.repository.delete(config_id)
            logger.info(f"删除 LLM 配置: {config.name} (ID: {config_id})")
            return True
            
        except Exception as e:
            logger.error(f"删除 LLM 配置失败: {e}")
            raise
    
    def get_config(self, config_id: UUID, decrypt_api_key: bool = False) -> Optional[LLMConfig]:
        """获取 LLM 配置"""
        config = self.repository.get(config_id)
        if config and decrypt_api_key and config.api_key:
            # 解密 API 密钥（仅在需要时）
            config.api_key = encryption.decrypt(config.api_key)
        return config
    
    def get_config_by_name(self, name: str, decrypt_api_key: bool = False) -> Optional[LLMConfig]:
        """根据名称获取配置"""
        config = self.repository.get_by_name(name)
        if config and decrypt_api_key and config.api_key:
            config.api_key = encryption.decrypt(config.api_key)
        return config
    
    def get_active_configs(
        self, 
        is_embedding: Optional[bool] = None,
        decrypt_api_key: bool = False
    ) -> List[LLMConfig]:
        """获取所有激活的配置"""
        configs = self.repository.get_active_configs(is_embedding)
        if decrypt_api_key:
            for config in configs:
                if config.api_key:
                    config.api_key = encryption.decrypt(config.api_key)
        return configs
    
    def get_default_config(
        self, 
        is_embedding: bool = False,
        decrypt_api_key: bool = False
    ) -> Optional[LLMConfig]:
        """获取默认配置"""
        config = self.repository.get_default_config(is_embedding)
        if config and decrypt_api_key and config.api_key:
            config.api_key = encryption.decrypt(config.api_key)
        return config
    
    def search_configs(
        self,
        search: Optional[str] = None,
        provider: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_embedding: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[LLMConfig]:
        """搜索配置"""
        return self.repository.search_configs(
            search=search,
            provider=provider,
            is_active=is_active,
            is_embedding=is_embedding,
            skip=skip,
            limit=limit
        )
    
    def toggle_active(self, config_id: UUID) -> LLMConfig:
        """切换配置激活状态"""
        return self.repository.toggle_active(config_id)
    
    def set_as_default(self, config_id: UUID) -> LLMConfig:
        """设置为默认配置"""
        config = self.repository.get(config_id)
        if not config:
            raise ValueError(f"配置不存在: {config_id}")
        
        if not config.is_active:
            raise ValueError("只能将激活的配置设为默认")
        
        return self.repository.set_default(
            config_id=config_id,
            is_embedding=config.is_embedding,
            set_default=True
        )
    
    # ==================== 模型实例化 ====================
    
    def get_chat_model(
        self,
        config_id: Optional[UUID] = None,
        config_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        streaming: bool = False
    ) -> ChatOpenAI:
        """获取聊天模型实例"""
        try:
            # 获取配置
            if config_id:
                config = self.get_config(config_id, decrypt_api_key=True)
            elif config_name:
                config = self.get_config_by_name(config_name, decrypt_api_key=True)
            else:
                config = self.get_default_config(is_embedding=False, decrypt_api_key=True)
            
            if not config:
                raise ValueError("未找到可用的 LLM 配置")
            
            if not config.is_active:
                raise ValueError(f"配置 '{config.name}' 未激活")
            
            if config.is_embedding:
                raise ValueError(f"配置 '{config.name}' 是嵌入模型，不能用于聊天")
            
            # 记录使用
            self.repository.increment_usage(config.id)
            
            # 创建模型实例
            return ChatOpenAI(
                model=config.model_name,
                api_key=config.api_key or "dummy-key",
                base_url=config.base_url,
                temperature=temperature if temperature is not None else config.temperature,
                max_tokens=max_tokens if max_tokens is not None else config.max_tokens,
                model_kwargs={
                    "top_p": config.top_p,
                    "frequency_penalty": config.frequency_penalty,
                    "presence_penalty": config.presence_penalty,
                    **(config.extra_config or {})
                },
                streaming=streaming
            )
            
        except Exception as e:
            logger.error(f"获取聊天模型失败: {e}")
            raise
    
    def get_embedding_model(
        self,
        config_id: Optional[UUID] = None,
        config_name: Optional[str] = None
    ) -> Embeddings:
        """获取嵌入模型实例"""
        try:
            # 获取配置
            if config_id:
                config = self.get_config(config_id, decrypt_api_key=True)
            elif config_name:
                config = self.get_config_by_name(config_name, decrypt_api_key=True)
            else:
                config = self.get_default_config(is_embedding=True, decrypt_api_key=True)
            
            if not config:
                raise ValueError("未找到可用的嵌入模型配置")
            
            if not config.is_active:
                raise ValueError(f"配置 '{config.name}' 未激活")
            
            if not config.is_embedding:
                raise ValueError(f"配置 '{config.name}' 不是嵌入模型")
            
            # 记录使用
            self.repository.increment_usage(config.id)
            
            # 根据提供商创建嵌入模型
            from langchain_openai import OpenAIEmbeddings
            
            return OpenAIEmbeddings(
                model=config.model_name,
                api_key=config.api_key or "dummy-key",
                base_url=config.base_url
            )
            
        except Exception as e:
            logger.error(f"获取嵌入模型失败: {e}")
            raise

