"""
聊天 API — RAG 问答
Author: ch

端点:
  POST /api/v1/chat/send  — 发送问题，获取 RAG 增强回答

学习要点:
  1. Pydantic Field 验证:
     - min_length/max_length → 防止空问题和过长输入
     - ge/le → 限制 top_k 范围
     - default_factory → 可变默认值（list 不能用 []，要 list factory）
  2. Request/Response 分离: 请求模型在路由定义，响应模型复用 models 包
  3. 服务层返回 ChatResult → 路由直接 return，无需转换
"""

import logging

from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.models.chat import ChatResult
from backend.services.chat_service import chat

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


# ── 请求模型（只属于路由层） ──

class ChatRequest(BaseModel):
    """聊天请求"""
    question: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="用户问题（1-5000字）",
    )
    conversation_id: str | None = Field(
        default=None,
        description="会话 ID，Phase 2 支持多会话后使用",
    )
    chat_history: list[dict] = Field(
        default_factory=list,
        description="对话历史: [{'role':'user'|'assistant','content':'...'}]",
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="检索文档块数量: 越大上下文越丰富但越慢",
    )


# ── 路由 ──

@router.post("/send", response_model=ChatResult)
async def send_message(req: ChatRequest):
    """
    发送问题，获取 RAG 增强回答

    请求示例:
      {"question": "退款政策是什么？", "top_k": 5, "chat_history": []}

    响应示例:
      {
        "answer": "根据产品手册，退款政策是...",
        "sources": [{"document_name": "产品手册.pdf", "score": 0.95, ...}]
      }
    """
    logger.info("收到聊天请求 | question=%.100s... | top_k=%d",
                req.question, req.top_k)

    return await chat(
        question=req.question,
        chat_history=req.chat_history,
        top_k=req.top_k,
    )
