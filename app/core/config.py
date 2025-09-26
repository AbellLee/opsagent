import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # 数据库配置
    database_url: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5733/opsagent")
    
    # API配置
    api_key: Optional[str] = os.getenv("API_KEY")
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # 日志配置
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # 通义模型配置
    tongyi_api_key: Optional[str] = os.getenv("TONGYI_API_KEY")
    tongyi_model_name: str = os.getenv("TONGYI_MODEL_NAME", "qwen-plus")
    
    class Config:
        # 修复env_file路径，使用相对路径
        env_file = ".env"

# 延迟初始化配置
_settings = None

def get_settings():
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

settings = get_settings()