from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import ConfigDict
import os

# 确保在加载配置前加载.env文件
from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):
    # 数据库配置
    database_url: str = os.getenv("DATABASE_URL", "postgresql://opsagent:opsagent@localhost:5432/opsagent")
    
    # 通义千问配置（保持向后兼容）
    tongyi_api_key: Optional[str] = os.getenv("DASHSCOPE_API_KEY")
    tongyi_model_name: str = os.getenv("TONGYI_MODEL_NAME", "qwen-plus")
    
    # 新的LLM配置
    llm_type: str = os.getenv("LLM_TYPE", "tongyi")
    llm_api_key: Optional[str] = os.getenv("LLM_API_KEY")
    llm_model: Optional[str] = os.getenv("LLM_MODEL")
    llm_base_url: Optional[str] = os.getenv("LLM_BASE_URL")
    llm_embedding_model: Optional[str] = os.getenv("LLM_EMBEDDING_MODEL")
    llm_timeout: int = int(os.getenv("LLM_TIMEOUT", "60"))
    llm_max_retries: int = int(os.getenv("LLM_MAX_RETRIES", "2"))
    
    # API配置
    api_key: Optional[str] = os.getenv("API_KEY")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # JWT配置（占位符，实际项目中需要配置）
    jwt_secret_key: str = "your-secret-key"
    jwt_algorithm: str = "HS256"
    
    model_config = ConfigDict(env_file=".env", extra="ignore")

# 全局配置实例
settings = Settings()