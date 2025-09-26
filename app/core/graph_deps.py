from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore
from contextlib import asynccontextmanager
from fastapi import FastAPI 
from .config import settings

# 全局单例
app_store: PostgresStore | None = None
app_checkpointer: PostgresSaver | None = None

@asynccontextmanager
async def init_graph_components(app: FastAPI):
    """用于 lifespan 初始化"""
    global app_store, app_checkpointer
    app_store = PostgresStore.from_conn_string(settings.database_url)
    app_checkpointer = PostgresSaver.from_conn_string(settings.database_url)
    yield
    # 可选：清理（通常不需要）