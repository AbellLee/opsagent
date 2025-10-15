"""
应用启动脚本 - 设置Windows事件循环策略
"""
import asyncio
import platform

# Windows平台需要设置事件循环策略以支持psycopg异步操作
# 必须在导入FastAPI和uvicorn之前设置
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    print("已设置Windows SelectorEventLoop策略")

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

