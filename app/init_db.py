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

        # 启用UUID扩展
        cursor.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")

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

        # 创建 LLM 配置表（必须在 user_sessions 之前创建，因为有外键引用）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS llm_configs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(100) NOT NULL UNIQUE,
                provider VARCHAR(50) NOT NULL,
                model_name VARCHAR(100) NOT NULL,
                api_key VARCHAR(500),
                base_url VARCHAR(200),
                max_tokens INTEGER NOT NULL DEFAULT 2048,
                temperature FLOAT NOT NULL DEFAULT 0.7,
                top_p FLOAT NOT NULL DEFAULT 1.0,
                frequency_penalty FLOAT NOT NULL DEFAULT 0.0,
                presence_penalty FLOAT NOT NULL DEFAULT 0.0,
                description TEXT,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                is_default BOOLEAN NOT NULL DEFAULT FALSE,
                is_embedding BOOLEAN NOT NULL DEFAULT FALSE,
                extra_config JSONB,
                usage_count INTEGER NOT NULL DEFAULT 0,
                last_used_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                created_by UUID,
                updated_by UUID,
                CONSTRAINT check_provider CHECK (provider IN ('openai', 'deepseek', 'tongyi', 'ollama', 'vllm', 'doubao', 'zhipu', 'moonshot', 'baidu'))
            )
        """)

        # 创建 LLM 配置表索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_llm_configs_provider ON llm_configs(provider)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_llm_configs_is_active ON llm_configs(is_active)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_llm_configs_is_default_embedding ON llm_configs(is_default, is_embedding)
        """)

        # 创建更新时间触发器函数（如果不存在）
        cursor.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            $$ language 'plpgsql'
        """)

        # 为 llm_configs 表创建触发器
        cursor.execute("""
            DROP TRIGGER IF EXISTS update_llm_configs_updated_at ON llm_configs
        """)
        cursor.execute("""
            CREATE TRIGGER update_llm_configs_updated_at
            BEFORE UPDATE ON llm_configs
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
        """)

        # 创建用户会话关系表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id UUID PRIMARY KEY,
                session_name VARCHAR(100) NOT NULL DEFAULT '新建对话',
                user_id UUID NOT NULL REFERENCES users(user_id),
                llm_config_id UUID REFERENCES llm_configs(id),
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

        # 创建MCP服务器配置表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mcp_server_configs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(100) UNIQUE NOT NULL,
                description TEXT,
                config JSONB NOT NULL,
                enabled BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建任务表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id VARCHAR(8) PRIMARY KEY,
                user_id UUID REFERENCES users(user_id),
                session_id UUID,
                content TEXT NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
                parent_task_id VARCHAR(8) REFERENCES tasks(id),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
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
        # 直接使用 PostgresSaver 初始化检查点表
        from langgraph.checkpoint.postgres import PostgresSaver
        
        with PostgresSaver.from_conn_string(settings.database_url) as checkpointer:
            checkpointer.setup()
            logger.info("检查点表初始化完成")
    except ImportError:
        logger.warning("未安装 langgraph 或 langgraph-checkpoint-postgres，跳过检查点表初始化")
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
        return True
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)