"""小暖 WebSocket — 流式对话"""
import logging, json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from langchain_core.messages import HumanMessage, AIMessage
from backend.agents.orchestrator import chat_stream

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/v1/gf/chat")
async def gf_ws(ws: WebSocket):
    await ws.accept()
    logger.info("WebSocket 已连接")

    try:
        while True:
            raw = await ws.receive_text()
            req = json.loads(raw)
            message = req.get("message", "")
            history = req.get("chat_history", [])

            msgs = []
            for m in history:
                if m["role"] == "user":
                    msgs.append(HumanMessage(content=m["content"]))
                else:
                    msgs.append(AIMessage(content=m["content"]))

            async for event in chat_stream(message, msgs):
                await ws.send_text(event.model_dump_json())

    except WebSocketDisconnect:
        logger.info("WebSocket 已断开")
    except Exception as e:
        logger.error("WebSocket 异常: %s", e)
