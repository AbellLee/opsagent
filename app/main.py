import sys
import os
import traceback
from contextlib import asynccontextmanager

# 将项目根目录添加到Python路径中
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import api_router
from app.core.llm import get_llm, LLMInitializationError, set_pre_initialized_llm
from app.core.logger import logger

from app.core.instances import set_llm_instance

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    # 启动时执行
    try:
        logger.info("正在初始化模型...")
        llm_instance, embedding_instance = get_llm()
        # 设置预初始化的LLM实例
        set_pre_initialized_llm(llm_instance, embedding_instance)
        set_llm_instance(llm_instance, embedding_instance)
        logger.info("LLM初始化完成")
        
        # Graph实例在需要时动态创建，无需预初始化
        logger.info("Graph将在需要时动态创建")
    except LLMInitializationError as e:
        logger.error(f"LLM初始化失败: {e}")
    except Exception as e:
        logger.error(f"初始化过程中发生未知错误: {e}")
        logger.error(traceback.format_exc())
    
    yield
    
    # 关闭时执行
    logger.info("应用正在关闭...")
    # 注意：PostgresSaver可能没有显式的关闭方法，这里只是示例
    # 在实际应用中，可能需要根据具体实现来处理资源清理

app = FastAPI(
    title="OpsAgent API",
    description="基于langgraph、fastapi和postgresql构建的Agent系统",
    version="0.1.0",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含API路由
app.include_router(api_router)

@app.get("/")
async def root():
    return {"message": "Welcome to OpsAgent API"}

@app.get("/health")
async def health_check():
    from app.core.instances import llm_instance
    return {"status": "healthy", "llm_initialized": llm_instance is not None}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)