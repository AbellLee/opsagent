from typing import Optional, Tuple, Dict, Any
import logging
import os

logger = logging.getLogger(__name__)

class LLMConfig:
    """LLM配置类，用于管理不同供应商的默认配置"""
    def __init__(
        self,
        default_chat_model: Optional[str] = None,
        default_embedding_model: Optional[str] = None,
        provider_package: Optional[str] = None,
        needs_base_url: bool = True,
        api_key_env_fallbacks: Optional[list] = None,
    ):
        self.default_chat_model = default_chat_model
        self.default_embedding_model = default_embedding_model
        self.provider_package = provider_package
        self.needs_base_url = needs_base_url
        self.api_key_env_fallbacks = api_key_env_fallbacks or []

# 模型配置字典（仅保留默认值，环境变量优先）
MODEL_CONFIGS: Dict[str, LLMConfig] = {
    "openai": LLMConfig(
        default_chat_model="gpt-4o-mini",
        default_embedding_model="text-embedding-3-small",
        provider_package="langchain_openai",
        needs_base_url=True,
        api_key_env_fallbacks=["OPENAI_API_KEY"],
    ),
    "deepseek": LLMConfig(
        default_chat_model="deepseek-chat",
        default_embedding_model=None,
        provider_package="langchain_deepseek",
        needs_base_url=True,
        api_key_env_fallbacks=["DEEPSEEK_API_KEY"],
    ),
    "ollama": LLMConfig(
        default_chat_model="llama3",
        default_embedding_model=None,
        provider_package="langchain_ollama",
        needs_base_url=True,
        api_key_env_fallbacks=[],
    ),
    "tongyi": LLMConfig(
        default_chat_model="qwen-turbo",
        default_embedding_model="text-embedding-v1",
        provider_package="langchain_community.chat_models.tongyi",
        needs_base_url=False,  # 通义不需要 base_url
        api_key_env_fallbacks=["DASHSCOPE_API_KEY"],
    ),
    "vllm": LLMConfig(
        default_chat_model="llama3",
        default_embedding_model=None,
        provider_package="langchain_openai",
        needs_base_url=True,
        api_key_env_fallbacks=["VLLM_API_KEY"],
    ),
}

DEFAULT_LLM_TYPE = "tongyi"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TIMEOUT = 60
DEFAULT_MAX_RETRIES = 2

class LLMInitializationError(Exception):
    pass

_pre_initialized_llm = None
_pre_initialized_embedding = None

def set_pre_initialized_llm(llm, embedding):
    global _pre_initialized_llm, _pre_initialized_embedding
    _pre_initialized_llm = llm
    _pre_initialized_embedding = embedding

def get_pre_initialized_llm():
    global _pre_initialized_llm, _pre_initialized_embedding
    return _pre_initialized_llm, _pre_initialized_embedding

def _resolve_api_key(llm_type: str, config: LLMConfig) -> str:
    # 优先使用统一的 LLM_API_KEY
    api_key = os.getenv("LLM_API_KEY")
    if api_key:
        return api_key

    # 尝试 fallback 环境变量
    for env_var in config.api_key_env_fallbacks:
        key = os.getenv(env_var)
        if key:
            return key

    # vLLM 特殊处理：默认为 "EMPTY"
    if llm_type == "vllm":
        return "EMPTY"

    # 构建错误信息
    attempted = ["LLM_API_KEY"] + config.api_key_env_fallbacks
    raise ValueError(f"缺少API密钥。尝试了环境变量: {', '.join(attempted)}")

def _resolve_base_url(llm_type: str, config: LLMConfig) -> Optional[str]:
    if not config.needs_base_url:
        return None

    # 优先从环境变量获取
    base_url = os.getenv("LLM_BASE_URL") or os.getenv("LLM_URL")
    if base_url:
        return base_url.strip()

    # 各模型默认地址（仅当无环境变量时使用）
    defaults = {
        "ollama": "http://localhost:11434/v1",
        "vllm": "http://localhost:8000/v1",
        "openai": "https://api.openai.com/v1",
        "deepseek": "https://api.deepseek.com/v1",
    }
    return defaults.get(llm_type)

def _resolve_models(config: LLMConfig) -> Tuple[Optional[str], Optional[str]]:
    chat_model = os.getenv("LLM_MODEL") or config.default_chat_model
    embedding_model = os.getenv("LLM_EMBEDDING_MODEL") or config.default_embedding_model
    return chat_model, embedding_model

def initialize_llm(llm_type: str = DEFAULT_LLM_TYPE) -> Tuple[Any, Optional[Any]]:
    if llm_type not in MODEL_CONFIGS:
        raise ValueError(f"不支持的LLM类型: {llm_type}. 支持: {list(MODEL_CONFIGS.keys())}")

    config = MODEL_CONFIGS[llm_type]

    try:
        api_key = _resolve_api_key(llm_type, config)
        base_url = _resolve_base_url(llm_type, config)
        chat_model, embedding_model = _resolve_models(config)

        if config.needs_base_url and not base_url:
            raise ValueError("该模型类型需要 base_url，但未通过 LLM_BASE_URL 环境变量或默认值提供")

        if not chat_model:
            raise ValueError("未指定聊天模型（通过 LLM_MODEL 环境变量或默认配置）")

        timeout = int(os.getenv("LLM_TIMEOUT", DEFAULT_TIMEOUT))
        max_retries = int(os.getenv("LLM_MAX_RETRIES", DEFAULT_MAX_RETRIES))

        # 初始化具体 LLM
        if llm_type == "openai":
            from langchain_openai import ChatOpenAI, OpenAIEmbeddings
            llm = ChatOpenAI(
                base_url=base_url,
                api_key=api_key,
                model=chat_model,
                temperature=DEFAULT_TEMPERATURE,
                timeout=timeout,
                max_retries=max_retries,
            )
            embedding = (
                OpenAIEmbeddings(base_url=base_url, api_key=api_key, model=embedding_model)
                if embedding_model else None
            )

        elif llm_type == "deepseek":
            from langchain_deepseek import ChatDeepSeek
            llm = ChatDeepSeek(
                api_key=api_key,
                model=chat_model,
                temperature=DEFAULT_TEMPERATURE,
                timeout=timeout,
                max_retries=max_retries,
            )
            embedding = None

        elif llm_type == "ollama":
            from langchain_ollama import ChatOllama
            llm = ChatOllama(
                base_url=base_url,
                model=chat_model,
                temperature=DEFAULT_TEMPERATURE,
                timeout=timeout,
            )
            embedding = None

        elif llm_type == "tongyi":
            from langchain_community.chat_models import ChatTongyi
            # 通义千问通过 DASHSCOPE_API_KEY 或 LLM_API_KEY 设置
            os.environ["DASHSCOPE_API_KEY"] = api_key  # 确保底层能读到
            llm = ChatTongyi(
                model=chat_model,
                temperature=DEFAULT_TEMPERATURE,
                timeout=timeout,
                max_retries=max_retries,
            )
            embedding = None

        elif llm_type == "vllm":
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                base_url=base_url,
                api_key=api_key,
                model=chat_model,
                temperature=DEFAULT_TEMPERATURE,
                timeout=timeout,
                max_retries=max_retries,
            )
            embedding = None

        logger.info(f"成功初始化 {llm_type} LLM，模型: {chat_model}，base_url: {base_url}")
        return llm, embedding

    except Exception as e:
        logger.error(f"初始化LLM失败 ({llm_type}): {e}")
        raise LLMInitializationError(f"初始化LLM失败: {e}")

def get_llm(llm_type: Optional[str] = None) -> Tuple[Any, Optional[Any]]:
    pre_llm, pre_embedding = get_pre_initialized_llm()
    if pre_llm is not None:
        return pre_llm, pre_embedding

    # 从 settings 或环境变量获取 llm_type
    if not llm_type:
        from app.core.config import settings
        llm_type = getattr(settings, 'llm_type', os.getenv("LLM_TYPE", DEFAULT_LLM_TYPE))

    try:
        return initialize_llm(llm_type)
    except LLMInitializationError:
        if llm_type != DEFAULT_LLM_TYPE:
            logger.warning(f"回退到默认 LLM 类型: {DEFAULT_LLM_TYPE}")
            return initialize_llm(DEFAULT_LLM_TYPE)
        raise