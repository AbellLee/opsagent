#!/usr/bin/env python3
"""为 user_sessions 表添加 llm_config_id 字段"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import psycopg2
from core.config import get_settings
from core.logger import logger

def main():
    settings = get_settings()
    conn = psycopg2.connect(settings.database_url)
    cur = conn.cursor()
    
    try:
        # 检查字段是否已存在
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='user_sessions' AND column_name='llm_config_id'
        """)
        result = cur.fetchone()
        
        if result:
            logger.info("✓ llm_config_id 字段已存在")
        else:
            logger.info("正在添加 llm_config_id 字段...")
            cur.execute("""
                ALTER TABLE user_sessions 
                ADD COLUMN llm_config_id UUID REFERENCES llm_configs(id)
            """)
            conn.commit()
            logger.info("✓ llm_config_id 字段添加成功")
        
        # 显示更新后的表结构
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name='user_sessions' 
            ORDER BY ordinal_position
        """)
        columns = cur.fetchall()
        logger.info("\nuser_sessions 表结构:")
        for col in columns:
            nullable = "NULL" if col[2] == "YES" else "NOT NULL"
            logger.info(f"  - {col[0]}: {col[1]} {nullable}")
            
    except Exception as e:
        conn.rollback()
        logger.error(f"添加字段失败: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()

