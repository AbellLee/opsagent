from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.llms import Tongyi
from typing import Optional, Tuple
import logging
import os

# 设置日志
logger = logging.getLogger(__name__)

# 模型配置字典
MODEL_CONFIGS = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "api_key_env": "LLM_API_KEY",  # 统一使用LLM_API_KEY
        "default_chat_model": "gpt-4o-mini",
        "default_embedding_model": "text-embedding-3-small"
    },
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key_env": "LLM_API_KEY",  # 统一使用LLM_API_KEY
        "default_chat_model": "qwen-plus",
        "default_embedding_model": "text-embedding-v1"
    },
    "oneapi": {
        "base_url": None,  # 需要从环境变量获取
        "api_key_env": "LLM_API_KEY",  # 统一使用LLM_API_KEY
        "default_chat_model": "qwen-plus",
        "default_embedding_model": "text-embedding-v1"
    },
    "tongyi": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key_env": "LLM_API_KEY",  # 统一使用LLM_API_KEY，也兼容DASHSCOPE_API_KEY
        "default_chat_model": "qwen-plus",
        "default_embedding_model": "text-embedding-v1"
    },
    "custom": {
        "base_url": None,  # 需要从环境变量获取
        "api_key_env": "LLM_API_KEY",  # 统一使用LLM_API_KEY
        "default_chat_model": None,  # 需要从环境变量获取
        "default_embedding_model": None  # 需要从环境变量获取
    }
}

# 默认配置
DEFAULT_LLM_TYPE = "qwen"
DEFAULT_TEMPERATURE = 0.7

class LLMInitializationError(Exception):
    """自定义异常类用于LLM初始化错误"""
    pass

# 存储预初始化的LLM实例
_pre_initialized_llm = None
_pre_initialized_embedding = None

def set_pre_initialized_llm(llm, embedding):
    """
    设置预初始化的LLM实例
    
    Args:
        llm: 预初始化的LLM实例
        embedding: 预初始化的嵌入模型实例
    """
    global _pre_initialized_llm, _pre_initialized_embedding
    _pre_initialized_llm = llm
    _pre_initialized_embedding = embedding

def get_pre_initialized_llm():
    """
    获取预初始化的LLM实例
    
    Returns:
        Tuple[ChatOpenAI, OpenAIEmbeddings]: 预初始化的LLM和嵌入模型实例
    """
    global _pre_initialized_llm, _pre_initialized_embedding
    return _pre_initialized_llm, _pre_initialized_embedding

def initialize_llm(llm_type: str = DEFAULT_LLM_TYPE) -> Tuple[ChatOpenAI, OpenAIEmbeddings]:
    """
    初始化LLM实例
    
    Args:
        llm_type (str): LLM类型
        
    Returns:
        Tuple[ChatOpenAI, OpenAIEmbeddings]: LLM和嵌入模型实例
        
    Raises:
        LLMInitializationError: 当LLM初始化失败时抛出
    """
    try:
        # 检查llm_type是否有效
        if llm_type not in MODEL_CONFIGS:
            raise ValueError(f"不支持的LLM类型: {llm_type}. 可用的类型: {list(MODEL_CONFIGS.keys())}")

        config = MODEL_CONFIGS[llm_type]
        
        # 获取API密钥（优先使用LLM_API_KEY）
        api_key = os.getenv("LLM_API_KEY")
        
        # 如果没有找到LLM_API_KEY，根据llm_type尝试其他可能的环境变量
        if not api_key:
            if llm_type in ["tongyi", "qwen"]:
                # 兼容阿里云的DASHSCOPE_API_KEY
                api_key = os.getenv("DASHSCOPE_API_KEY")
            elif llm_type == "openai":
                # 兼容OpenAI的原始环境变量
                api_key = os.getenv("OPENAI_API_KEY")
                
        if not api_key:
            # 构建详细的错误消息，包含所有尝试过的环境变量名
            attempted_vars = ["LLM_API_KEY"]
            if llm_type in ["tongyi", "qwen"]:
                attempted_vars.append("DASHSCOPE_API_KEY")
            if llm_type == "openai":
                attempted_vars.append("OPENAI_API_KEY")
                
            raise ValueError(f"缺少API密钥环境变量。已尝试查找: {', '.join(attempted_vars)}")

        # 获取base_url（如果需要）
        base_url = config["base_url"] or os.getenv("LLM_BASE_URL")
        if not base_url and llm_type == "custom":
            raise ValueError(f"缺少base_url配置或环境变量")

        # 获取模型名称（优先使用环境变量LLM_MODEL，否则使用默认值）
        chat_model = os.getenv("LLM_MODEL") or config["default_chat_model"]
        if not chat_model and llm_type == "custom":
            raise ValueError(f"缺少chat_model配置或环境变量")

        embedding_model = os.getenv("LLM_EMBEDDING_MODEL") or config["default_embedding_model"]
        if not embedding_model and llm_type == "custom":
            raise ValueError(f"缺少embedding_model配置或环境变量")

        # 特殊处理 tongyi 类型（使用专门的Tongyi类）
        if llm_type == "tongyi":
            # 确保dashscope相关的环境变量都设置好
            os.environ['DASHSCOPE_API_KEY'] = api_key
            if 'LLM_API_KEY' not in os.environ:
                os.environ['LLM_API_KEY'] = api_key
            
            llm = Tongyi(
                dashscope_api_key=api_key,
                model_name=chat_model
            )
            # Tongyi不支持嵌入模型，返回None
            return llm, None

        # 创建LLM实例
        llm = ChatOpenAI(
            base_url=base_url,
            api_key=api_key,
            model=chat_model,
            temperature=DEFAULT_TEMPERATURE,
            timeout=30,
            max_retries=2
        )

        # 创建嵌入模型实例
        embedding = OpenAIEmbeddings(
            base_url=base_url,
            api_key=api_key,
            model=embedding_model
        )

        logger.info(f"成功初始化 {llm_type} LLM，模型: {chat_model}")
        return llm, embedding

    except ValueError as ve:
        logger.error(f"LLM配置错误: {str(ve)}")
        raise LLMInitializationError(f"LLM配置错误: {str(ve)}")
    except Exception as e:
        logger.error(f"初始化LLM失败: {str(e)}")
        raise LLMInitializationError(f"初始化LLM失败: {str(e)}")

def get_llm(llm_type: Optional[str] = None) -> Tuple[ChatOpenAI, OpenAIEmbeddings]:
    """
    获取LLM实例的封装函数
    优先使用预初始化的实例，如果没有则进行初始化
    
    Args:
        llm_type (str, optional): LLM类型
        
    Returns:
        Tuple[ChatOpenAI, OpenAIEmbeddings]: LLM和嵌入模型实例
    """
    # 首先尝试获取预初始化的实例
    pre_llm, pre_embedding = get_pre_initialized_llm()
    if pre_llm is not None:
        return pre_llm, pre_embedding
    
    from app.core.config import settings
    
    # 如果没有指定llm_type，则从配置中获取
    if not llm_type:
        llm_type = getattr(settings, 'llm_type', DEFAULT_LLM_TYPE)
    
    try:
        return initialize_llm(llm_type)
    except LLMInitializationError:
        logger.warning(f"使用默认配置重试: {llm_type}")
        if llm_type != DEFAULT_LLM_TYPE:
            return initialize_llm(DEFAULT_LLM_TYPE)
        raise