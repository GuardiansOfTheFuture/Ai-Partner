"""
健康检查 API
Author: ch

端点:
  GET /api/v1/health  — 服务健康检查
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(default="ok", description="服务状态: ok / error")
    version: str = Field(default="1.0.0", description="服务版本号")


@router.get("/api/v1/health", response_model=HealthResponse)
async def health():
    """
    健康检查 — 返回服务状态

    用途:
      1. 确认服务已启动
      2. 负载均衡器用它探测后端存活
      3. K8s liveness probe

    请求示例:
      GET /api/v1/health

    响应示例:
      {"status": "ok", "version": "1.0.0"}
    """
    return HealthResponse()
