"""创建 LLM 配置表"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from db.base import engine, Base
from models.database.llm_config import LLMConfig
from core.logger import logger

def create_tables():
    """创建所有表"""
    try:
        logger.info("开始创建数据库表...")
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建成功！")
        
        # 验证表是否创建
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"当前数据库表: {tables}")
        
        if 'llm_configs' in tables:
            logger.info("✓ llm_configs 表创建成功")
        else:
            logger.error("✗ llm_configs 表创建失败")
            
    except Exception as e:
        logger.error(f"创建表失败: {e}")
        raise

if __name__ == "__main__":
    create_tables()

