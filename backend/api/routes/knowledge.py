"""
知识库管理 API
Author: ch

端点:
  GET /api/v1/knowledge/stats  — 知识库统计信息
"""

import logging

from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.core.vector_store import get_collection_stats

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])


class KnowledgeStatsResponse(BaseModel):
    """知识库统计响应"""
    collection_name: str = Field(..., description="ChromaDB 集合名")
    total_chunks: int = Field(..., description="已入库的文档块总数")


@router.get("/stats", response_model=KnowledgeStatsResponse)
async def stats():
    """
    知识库统计

    Returns:
        KnowledgeStatsResponse {
            collection_name: "knowledge_base",
            total_chunks: 42
        }
    """
    s = get_collection_stats()
    logger.debug("知识库统计 | collection=%s | chunks=%d", s["name"], s["count"])
    return KnowledgeStatsResponse(
        collection_name=s["name"],
        total_chunks=s["count"],
    )
