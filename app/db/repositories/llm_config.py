"""LLM 配置数据访问层"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.database.llm_config import LLMConfig
from .base import BaseRepository


class LLMConfigRepository(BaseRepository[LLMConfig]):
    """LLM 配置 Repository"""
    
    def __init__(self, db: Session):
        super().__init__(LLMConfig, db)
    
    def get_by_name(self, name: str) -> Optional[LLMConfig]:
        """根据名称获取配置"""
        return self.db.query(LLMConfig).filter(LLMConfig.name == name).first()
    
    def get_active_configs(self, is_embedding: Optional[bool] = None) -> List[LLMConfig]:
        """获取所有激活的配置"""
        query = self.db.query(LLMConfig).filter(LLMConfig.is_active == True)
        if is_embedding is not None:
            query = query.filter(LLMConfig.is_embedding == is_embedding)
        return query.order_by(LLMConfig.created_at).all()
    
    def get_default_config(self, is_embedding: bool = False) -> Optional[LLMConfig]:
        """获取默认配置"""
        return self.db.query(LLMConfig).filter(
            and_(
                LLMConfig.is_default == True,
                LLMConfig.is_embedding == is_embedding,
                LLMConfig.is_active == True
            )
        ).first()
    
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
        query = self.db.query(LLMConfig)
        
        # 搜索
        if search:
            query = query.filter(
                or_(
                    LLMConfig.name.ilike(f"%{search}%"),
                    LLMConfig.model_name.ilike(f"%{search}%"),
                    LLMConfig.description.ilike(f"%{search}%")
                )
            )
        
        # 服务商筛选
        if provider:
            query = query.filter(LLMConfig.provider == provider)
        
        # 状态筛选
        if is_active is not None:
            query = query.filter(LLMConfig.is_active == is_active)
        
        # 模型类型筛选
        if is_embedding is not None:
            query = query.filter(LLMConfig.is_embedding == is_embedding)
        
        # 排序和分页
        return query.order_by(LLMConfig.name).offset(skip).limit(limit).all()
    
    def set_default(self, config_id: str, is_embedding: bool = False) -> bool:
        """设置默认配置"""
        # 取消同类型的其他默认配置
        self.db.query(LLMConfig).filter(
            LLMConfig.is_embedding == is_embedding
        ).update({"is_default": False})
        
        # 设置新的默认配置
        config = self.get(config_id)
        if config and config.is_active:
            config.is_default = True
            self.db.commit()
            return True
        return False
    
    def increment_usage(self, config_id: str):
        """增加使用次数"""
        from sqlalchemy import func
        config = self.get(config_id)
        if config:
            config.usage_count += 1
            config.last_used_at = func.now()
            self.db.commit()
    
    def toggle_active(self, config_id: str) -> Optional[LLMConfig]:
        """切换激活状态"""
        config = self.get(config_id)
        if config:
            config.is_active = not config.is_active
            # 如果禁用了默认配置，取消默认标记
            if not config.is_active and config.is_default:
                config.is_default = False
            self.db.commit()
            self.db.refresh(config)
        return config

