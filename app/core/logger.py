"""日志配置模块

提供统一的日志配置和管理功能，支持控制台和文件日志输出。
"""
import logging
import sys
from pathlib import Path
from typing import Optional
from .config import settings


def setup_logger(
    name: str = "opsagent",
    level: Optional[str] = None,
    log_file: Optional[str] = None
) -> logging.Logger:
    """设置日志配置

    Args:
        name: Logger名称，默认为"opsagent"
        level: 日志级别，默认从settings读取。可选值：DEBUG, INFO, WARNING, ERROR, CRITICAL
        log_file: 日志文件路径（可选），为None时只输出到控制台

    Returns:
        配置好的logger实例

    Example:
        >>> logger = setup_logger("opsagent", "DEBUG", "/var/log/opsagent.log")
        >>> logger.info("Application started")
    """
    logger = logging.getLogger(name)

    # 清除已有的handlers，避免重复
    logger.handlers.clear()

    # 设置日志级别
    log_level = level or settings.log_level
    logger.setLevel(getattr(logging, log_level.upper()))

    # 创建格式化器（添加时间格式化）
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台处理器（输出到stdout）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器（可选）
    if log_file:
        log_path = Path(log_file)
        # 自动创建日志目录
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的logger实例

    为不同模块创建独立的logger，便于日志追踪和过滤。

    Args:
        name: 模块名称，会自动添加"opsagent."前缀

    Returns:
        Logger实例

    Example:
        >>> from app.core.logger import get_logger
        >>> logger = get_logger("agent.graph")
        >>> logger.info("Graph initialized")
        # 输出: 2024-01-01 12:00:00 - opsagent.agent.graph - INFO - Graph initialized

        >>> logger = get_logger("services.agent.handlers")
        >>> logger.debug("Processing request")
        # 输出: 2024-01-01 12:00:00 - opsagent.services.agent.handlers - DEBUG - Processing request
    """
    return logging.getLogger(f"opsagent.{name}")


# 创建全局logger实例
# 检查settings中是否配置了log_file
log_file_path = getattr(settings, 'log_file', None)
logger = setup_logger(log_file=log_file_path)