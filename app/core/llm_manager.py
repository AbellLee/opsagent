"""LLM 管理器 - 统一管理基于数据库配置和环境变量的 LLM"""
from typing import Optional, Tuple, Any
from uuid import UUID
from sqlalchemy.orm import Session

from core.llm import initialize_llm, get_pre_initialized_llm, DEFAULT_LLM_TYPE
from services.llm_service import LLMService
from core.logger import logger


class LLMManager:
    """
    LLM 管理器 - 提供统一的 LLM 获取接口
    
    优先级：
    1. 预初始化的 LLM（用于测试）
    2. 数据库中的 LLM 配置
    3. 环境变量配置（向后兼容）
    """
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.llm_service = LLMService(db) if db else None
    
    def get_chat_llm(
        self,
        config_id: Optional[UUID] = None,
        config_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        streaming: bool = False,
        fallback_to_env: bool = True
    ) -> Any:
        """
        获取聊天 LLM 实例
        
        Args:
            config_id: LLM 配置 ID
            config_name: LLM 配置名称
            temperature: 温度参数（覆盖配置）
            max_tokens: 最大 token 数（覆盖配置）
            streaming: 是否流式输出
            fallback_to_env: 如果数据库配置不可用，是否回退到环境变量配置
        
        Returns:
            LLM 实例
        """
        # 1. 检查预初始化的 LLM
        pre_llm, _ = get_pre_initialized_llm()
        if pre_llm is not None:
            logger.info("使用预初始化的 LLM")
            return pre_llm
        
        # 2. 尝试从数据库获取配置
        if self.llm_service:
            try:
                llm = self.llm_service.get_chat_model(
                    config_id=config_id,
                    config_name=config_name,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    streaming=streaming
                )
                logger.info(f"使用数据库配置的 LLM: {config_name or config_id or '默认'}")
                return llm
            except Exception as e:
                logger.warning(f"从数据库获取 LLM 配置失败: {e}")
                if not fallback_to_env:
                    raise
        
        # 3. 回退到环境变量配置
        if fallback_to_env:
            logger.info("回退到环境变量配置的 LLM")
            llm, _ = initialize_llm(DEFAULT_LLM_TYPE)
            return llm
        
        raise ValueError("无法获取 LLM 实例")
    
    def get_embedding_model(
        self,
        config_id: Optional[UUID] = None,
        config_name: Optional[str] = None,
        fallback_to_env: bool = True
    ) -> Any:
        """
        获取嵌入模型实例
        
        Args:
            config_id: LLM 配置 ID
            config_name: LLM 配置名称
            fallback_to_env: 如果数据库配置不可用，是否回退到环境变量配置
        
        Returns:
            嵌入模型实例
        """
        # 1. 检查预初始化的嵌入模型
        _, pre_embedding = get_pre_initialized_llm()
        if pre_embedding is not None:
            logger.info("使用预初始化的嵌入模型")
            return pre_embedding
        
        # 2. 尝试从数据库获取配置
        if self.llm_service:
            try:
                embedding = self.llm_service.get_embedding_model(
                    config_id=config_id,
                    config_name=config_name
                )
                logger.info(f"使用数据库配置的嵌入模型: {config_name or config_id or '默认'}")
                return embedding
            except Exception as e:
                logger.warning(f"从数据库获取嵌入模型配置失败: {e}")
                if not fallback_to_env:
                    raise
        
        # 3. 回退到环境变量配置
        if fallback_to_env:
            logger.info("回退到环境变量配置的嵌入模型")
            _, embedding = initialize_llm(DEFAULT_LLM_TYPE)
            if embedding is None:
                raise ValueError("环境变量配置中没有嵌入模型")
            return embedding
        
        raise ValueError("无法获取嵌入模型实例")
    
    def get_llm_and_embedding(
        self,
        config_id: Optional[UUID] = None,
        config_name: Optional[str] = None,
        fallback_to_env: bool = True
    ) -> Tuple[Any, Optional[Any]]:
        """
        同时获取聊天 LLM 和嵌入模型
        
        Args:
            config_id: LLM 配置 ID
            config_name: LLM 配置名称
            fallback_to_env: 如果数据库配置不可用，是否回退到环境变量配置
        
        Returns:
            (LLM 实例, 嵌入模型实例)
        """
        # 1. 检查预初始化
        pre_llm, pre_embedding = get_pre_initialized_llm()
        if pre_llm is not None:
            logger.info("使用预初始化的 LLM 和嵌入模型")
            return pre_llm, pre_embedding
        
        # 2. 尝试从数据库获取
        if self.llm_service:
            try:
                llm = self.get_chat_llm(
                    config_id=config_id,
                    config_name=config_name,
                    fallback_to_env=False
                )
                try:
                    embedding = self.get_embedding_model(
                        config_id=config_id,
                        config_name=config_name,
                        fallback_to_env=False
                    )
                except:
                    embedding = None
                return llm, embedding
            except Exception as e:
                logger.warning(f"从数据库获取 LLM 配置失败: {e}")
                if not fallback_to_env:
                    raise
        
        # 3. 回退到环境变量配置
        if fallback_to_env:
            logger.info("回退到环境变量配置")
            return initialize_llm(DEFAULT_LLM_TYPE)
        
        raise ValueError("无法获取 LLM 实例")


# 全局 LLM 管理器实例（用于无数据库会话的场景）
_global_llm_manager: Optional[LLMManager] = None


def get_global_llm_manager() -> LLMManager:
    """获取全局 LLM 管理器"""
    global _global_llm_manager
    if _global_llm_manager is None:
        _global_llm_manager = LLMManager()
    return _global_llm_manager


def set_global_llm_manager(manager: LLMManager):
    """设置全局 LLM 管理器"""
    global _global_llm_manager
    _global_llm_manager = manager

