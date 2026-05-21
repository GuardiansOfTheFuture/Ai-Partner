"""小暖 AI API"""
import logging
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, AIMessage
from backend.agents.orchestrator import chat, chat_stream, ChatResult

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/gf", tags=["小暖"])


class GfChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    chat_history: list[dict] = Field(default_factory=list)


def _to_lc(history: list[dict]) -> list:
    msgs = []
    for m in history:
        if m["role"] == "user":
            msgs.append(HumanMessage(content=m["content"]))
        else:
            msgs.append(AIMessage(content=m["content"]))
    return msgs


@router.post("/chat", response_model=ChatResult)
async def send_message(req: GfChatRequest):
    return await chat(req.message, _to_lc(req.chat_history))


@router.post("/stream")
async def send_message_stream(req: GfChatRequest):
    async def generate():
        async for event in chat_stream(req.message, _to_lc(req.chat_history)):
            yield f"data: {event.model_dump_json()}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
