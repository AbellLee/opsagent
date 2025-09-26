from fastapi import Depends, HTTPException, status
from typing import Generator
import psycopg2
from app.core.config import get_settings
from app.core.logger import logger

def get_db() -> Generator:
    """获取数据库连接"""
    conn = None
    try:
        # 记录当前加载的配置
        current_settings = get_settings()
        logger.info(f"当前数据库配置URL: {current_settings.database_url}")
        logger.info(f"尝试连接数据库...")
        conn = psycopg2.connect(current_settings.database_url)
        logger.info("数据库连接成功")
        yield conn
    except Exception as e:
        error_msg = f"数据库连接失败: {e}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"数据库连接失败: {str(e)}"
        )
    finally:
        if conn:
            conn.close()
            logger.info("数据库连接已关闭")