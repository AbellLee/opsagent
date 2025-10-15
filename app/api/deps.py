from fastapi import Depends, HTTPException, status
from typing import Generator
import psycopg2
import psycopg2.extras
from app.core.config import settings
from app.core.logger import logger

def get_db() -> Generator:
    """获取数据库连接"""
    conn = None
    try:
        # 记录当前加载的配置
        # logger.info(f"当前数据库配置URL: {settings.database_url}")
        # logger.info(f"尝试连接数据库...")
        conn = psycopg2.connect(settings.database_url)
        # 注册UUID适配器
        psycopg2.extras.register_uuid(conn_or_curs=conn)
        # logger.info("数据库连接成功")
        yield conn
    except Exception as e:
        error_msg = f"数据库连接失败: {e}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )
    finally:
        if conn:
            conn.close()

def get_settings():
    """获取全局配置"""
    return settings