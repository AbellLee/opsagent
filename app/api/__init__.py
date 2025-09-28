from fastapi import APIRouter
from app.api.routes import sessions, tools, users, agent, approvals

api_router = APIRouter()
# 先注册更具体的路由（带参数的）
api_router.include_router(agent.router)
# 再注册一般路由
api_router.include_router(sessions.router)
api_router.include_router(tools.router)
api_router.include_router(users.router)
api_router.include_router(approvals.router)

__all__ = ["api_router"]