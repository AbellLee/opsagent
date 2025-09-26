import logging
from app.core.config import settings

def setup_logger():
    """设置日志配置"""
    # 创建logger
    logger = logging.getLogger("opsagent")
    logger.setLevel(settings.log_level.upper())
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(settings.log_level.upper())
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    # 添加处理器到logger
    if not logger.handlers:
        logger.addHandler(console_handler)
    
    return logger

# 创建全局logger实例
logger = setup_logger()