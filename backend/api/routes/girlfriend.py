"""AI 女友 API"""
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.messages import HumanMessage, AIMessage
from backend.db.database import async_session
from backend.agents.orchestrator import chat, chat_stream, ChatResult
from backend.models import list_characters
from backend.api.routes.auth import verify_token, _tokens
from backend.services.chat_persistence import (
    list_conversations, get_messages,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/gf", tags=["AI女友"])


class GfChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    character_id: str = Field(default="sweet")
    chat_history: list[dict] = Field(default_factory=list)


def _to_lc(history: list[dict]) -> list:
    msgs = []
    for m in history:
        if m["role"] == "user":
            msgs.append(HumanMessage(content=m["content"]))
        else:
            msgs.append(AIMessage(content=m["content"]))
    return msgs


def _get_openid(token: str) -> str:
    if not token or not verify_token(token):
        raise HTTPException(status_code=401, detail="请先登录")
    return _tokens.get(token, "")


@router.get("/characters")
async def get_characters():
    return {"characters": await list_characters()}


@router.post("/chat", response_model=ChatResult)
async def send_message(req: GfChatRequest):
    return await chat(req.message, _to_lc(req.chat_history), req.character_id)


@router.post("/stream")
async def send_message_stream(req: GfChatRequest):
    async def generate():
        async for event in chat_stream(req.message, _to_lc(req.chat_history), req.character_id):
            yield f"data: {event.model_dump_json()}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── 对话历史 ──

@router.get("/conversations")
async def get_conversations(token: str = ""):
    """获取当前用户的对话列表"""
    openid = _get_openid(token)
    async with async_session() as db:
        from backend.services.chat_persistence import ensure_user
        user = await ensure_user(openid, db)
        convs = await list_conversations(user.id, db)
    return {"conversations": convs}


@router.get("/conversations/{conv_id}/messages")
async def get_conv_messages(conv_id: str, token: str = ""):
    """获取指定对话的消息历史"""
    _get_openid(token)
    async with async_session() as db:
        msgs = await get_messages(conv_id, db)
    return {"messages": msgs, "conversation_id": conv_id}
