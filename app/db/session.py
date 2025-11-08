"""数据库会话管理（兼容现有 psycopg2 和新的 SQLAlchemy）"""
from typing import Generator
import psycopg2
import psycopg2.extras
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.logger import logger
from .base import SessionLocal


def get_db_psycopg2() -> Generator:
    """获取 psycopg2 原生连接（保持向后兼容）"""
    conn = None
    try:
        conn = psycopg2.connect(settings.database_url)
        psycopg2.extras.register_uuid(conn_or_curs=conn)
        yield conn
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        raise
    finally:
        if conn:
            conn.close()


def get_db_sqlalchemy() -> Generator[Session, None, None]:
    """获取 SQLAlchemy 会话（用于新功能）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 别名，方便使用
get_db = get_db_psycopg2  # 默认使用 psycopg2（向后兼容）
get_db_orm = get_db_sqlalchemy  # 新功能使用 ORM

