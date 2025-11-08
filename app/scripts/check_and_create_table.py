#!/usr/bin/env python3
"""检查并创建 LLM 配置表"""
import psycopg2
import os

# 数据库连接
DATABASE_URL = "postgresql://root:Abell@652733@localhost:5432/opsagent"

def main():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # 检查表是否存在
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema='public' AND table_name='llm_configs'
    """)
    result = cur.fetchall()
    
    if result:
        print("✓ llm_configs 表已存在")
        # 显示表结构
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name='llm_configs' 
            ORDER BY ordinal_position
        """)
        columns = cur.fetchall()
        print("\n表结构:")
        for col in columns:
            print(f"  - {col[0]}: {col[1]}")
    else:
        print("✗ llm_configs 表不存在，正在创建...")
        # 读取并执行 SQL
        sql_file = os.path.join(os.path.dirname(__file__), 'create_llm_table.sql')
        with open(sql_file, 'r') as f:
            sql = f.read()
        cur.execute(sql)
        conn.commit()
        print("✓ 表创建成功！")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()

