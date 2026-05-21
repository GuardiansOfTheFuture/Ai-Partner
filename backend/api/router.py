"""主路由聚合"""
from fastapi import APIRouter
from backend.api.routes import health, girlfriend, gf_ws

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(girlfriend.router)
api_router.include_router(gf_ws.router)
