"""AI 女友 WebSocket — 流式对话 + MySQL 持久化"""
import logging, json, traceback
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from langchain_core.messages import HumanMessage, AIMessage
from backend.db.database import async_session
from backend.agents.orchestrator import chat_stream
from backend.api.routes.auth import verify_token
from backend.services.chat_persistence import (
    ensure_user, create_conversation, save_message,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# WebSocket 状态: 0=CONNECTING 1=CONNECTED 2=CLOSING 3=CLOSED
def _ws_alive(ws: WebSocket) -> bool:
    try:
        from starlette.websockets import WebSocketState
        return ws.client_state == WebSocketState.CONNECTED
    except ImportError:
        return True  # 旧版本 Starlette，假设活着


@router.websocket("/ws/v1/gf/chat")
async def gf_ws(ws: WebSocket):
    await ws.accept()
    first = True
    openid = ""
    conv_id = ""

    while True:
        try:
            raw = await ws.receive_text()
        except WebSocketDisconnect:
            break
        except Exception:
            break

        try:
            req = json.loads(raw)
        except json.JSONDecodeError:
            continue

        token = req.get("token", "")
        message = req.get("message", "")
        history = req.get("chat_history", [])
        character_id = req.get("character_id", "sweet")
        req_conv_id = req.get("conversation_id", "")

        if first:
            if not token or not verify_token(token):
                if _ws_alive(ws): await ws.send_text(json.dumps({"type": "error", "content": "请先登录"}))
                if _ws_alive(ws): await ws.close()
                return

            from backend.api.routes.auth import _tokens
            openid = _tokens.get(token, "")
            first = False

            async with async_session() as db:
                user = await ensure_user(openid, db)
                if req_conv_id:
                    conv_id = req_conv_id
                else:
                    conv = await create_conversation(user.id, character_id, db)
                    conv_id = conv.id
                    if _ws_alive(ws):
                        await ws.send_text(json.dumps({"type": "conv", "content": conv_id}))

        if not message:
            continue

        # 保存用户消息
        async with async_session() as db:
            await save_message(conv_id, "user", message, db=db)

        msgs = [HumanMessage(content=m["content"]) if m["role"] == "user" else AIMessage(content=m["content"])
                for m in history]

        # 流式生成
        full_response = ""
        voice_url = ""
        try:
            async for event in chat_stream(message, msgs, character_id):
                if _ws_alive(ws):
                    await ws.send_text(event.model_dump_json())
                else:
                    break
                if event.type == "token":
                    full_response += event.content
                elif event.type == "voice":
                    voice_url = event.content
        except Exception as e:
            logger.error("流式生成异常: %s", e)

        # 保存 AI 回复
        if full_response:
            try:
                async with async_session() as db:
                    await save_message(conv_id, "assistant", full_response, voice_url=voice_url, db=db)
            except Exception as e:
                logger.error("保存消息失败: %s", e)

    logger.info("WebSocket 已断开")
