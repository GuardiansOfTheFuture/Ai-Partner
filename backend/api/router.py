"""
主路由聚合 — 将所有子路由注册到同一个 APIRouter
Author: ch

设计意图:
  各模块各自管理自己的路由前缀和实现，
  这里只做聚合，不写业务逻辑。
  新增模块时只需加一行 include_router。
"""

from fastapi import APIRouter

from backend.api.routes import documents, chat, knowledge, health

api_router = APIRouter()

# 注册顺序不影响功能，但影响 Swagger 文档中的显示顺序
api_router.include_router(health.router)       # GET  /api/v1/health
api_router.include_router(documents.router)    # POST /api/v1/documents/...
api_router.include_router(chat.router)         # POST /api/v1/chat/...
api_router.include_router(knowledge.router)    # GET  /api/v1/knowledge/...
