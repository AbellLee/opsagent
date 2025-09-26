#!/usr/bin/env python3
"""
数据库初始化脚本
用于创建项目所需的数据表
"""

import sys
import os

# 将项目根目录添加到Python路径中
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
import psycopg
from psycopg2 import OperationalError
from app.core.config import get_settings
from app.core.logger import logger
import os as os_env

# 获取配置
settings = get_settings()

def check_database_connection():
    """检查数据库连接"""
    try:
        logger.info(f"尝试连接数据库: {settings.database_url}")
        logger.info(f"环境变量DATABASE_URL: {os_env.getenv('DATABASE_URL', '未设置')}")
        conn = psycopg2.connect(settings.database_url)
        conn.close()
        logger.info("数据库连接成功")
        return True
    except OperationalError as e:
        logger.error(f"数据库连接失败: {e}")
        return False
    except Exception as e:
        logger.error(f"数据库连接检查出现未知错误: {e}")
        return False

def create_tables():
    """创建数据库表"""
    conn = None
    try:
        # 连接数据库
        conn = psycopg2.connect(settings.database_url)
        cursor = conn.cursor()
        
        # 创建用户表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id UUID PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建用户会话关系表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id UUID PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES users(user_id),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                UNIQUE(session_id, user_id)
            )
        """)
        
        # 创建工具审批配置表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tool_approval_config (
                id UUID PRIMARY KEY,
                user_id UUID REFERENCES users(user_id),
                tool_id UUID NOT NULL,
                tool_name VARCHAR(100) NOT NULL,
                auto_execute BOOLEAN NOT NULL DEFAULT FALSE,
                approval_required BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, tool_id)
            )
        """)
        
        # 提交事务
        conn.commit()
        logger.info("数据库表创建成功")
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"创建数据库表失败: {e}")
        raise
    finally:
        if conn:
            cursor.close()
            conn.close()

def init_checkpointer_tables():
    """初始化检查点表（由langgraph自动创建）"""
    try:
        # 注意：langgraph的PostgresSaver会在首次使用时自动创建检查点表
        # 我们只需要确保数据库连接正常即可
        from app.agent.memory import memory_manager
        if memory_manager.checkpointer:
            memory_manager.setup()
            logger.info("检查点表初始化完成")
        else:
            logger.warning("检查点存储未初始化，跳过表初始化")
    except Exception as e:
        logger.error(f"初始化检查点表失败: {e}")
        raise

def main():
    """主函数"""
    logger.info("开始初始化数据库...")
    logger.info(f"当前工作目录: {os_env.getcwd()}")
    logger.info(f"配置文件路径: {os_env.path.join(os_env.getcwd(), '.env')}")
    logger.info(f"数据库URL配置: {settings.database_url}")
    
    try:
        # 检查数据库连接
        if not check_database_connection():
            logger.error("无法连接到数据库，请检查配置和网络连接")
            return False
            
        create_tables()
        init_checkpointer_tables()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        return False
    return True

if __name__ == "__main__":
    main()