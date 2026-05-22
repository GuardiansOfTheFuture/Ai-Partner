"""AI 女友 WebSocket — 流式对话 + MySQL 持久化"""
import logging, json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from langchain_core.messages import HumanMessage, AIMessage
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.database import async_session
from backend.agents.orchestrator import chat_stream
from backend.api.routes.auth import verify_token
from backend.services.chat_persistence import (
    ensure_user, create_conversation, save_message,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/v1/gf/chat")
async def gf_ws(ws: WebSocket):
    await ws.accept()

    try:
        # 第一条消息获取 token 和 openid
        first = True
        openid = ""
        conv_id = ""

        while True:
            raw = await ws.receive_text()
            req = json.loads(raw)

            token = req.get("token", "")
            message = req.get("message", "")
            history = req.get("chat_history", [])
            character_id = req.get("character_id", "sweet")
            req_conv_id = req.get("conversation_id", "")

            # 鉴权（首次）+ 获取 openid
            if first:
                if not token or not verify_token(token):
                    await ws.send_text(json.dumps({"type": "error", "content": "请先登录"}))
                    await ws.close()
                    return

                # 从 token 查出 openid，创建用户+会话
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
                        # 告诉前端会话 ID
                        await ws.send_text(json.dumps({"type": "conv", "content": conv_id}))

            msg = message
            if not msg:
                continue

            # 保存用户消息
            async with async_session() as db:
                await save_message(conv_id, "user", msg, db=db)

            # 构建 LangChain 消息
            msgs = []
            for m in history:
                if m["role"] == "user":
                    msgs.append(HumanMessage(content=m["content"]))
                else:
                    msgs.append(AIMessage(content=m["content"]))

            # 流式生成 + 收集回复
            full_response = ""
            voice_url = ""

            async for event in chat_stream(msg, msgs, character_id):
                await ws.send_text(event.model_dump_json())
                if event.type == "token":
                    full_response += event.content
                elif event.type == "voice":
                    voice_url = event.content

            # 保存 AI 回复
            if full_response:
                async with async_session() as db:
                    await save_message(
                        conv_id, "assistant", full_response,
                        voice_url=voice_url, db=db,
                    )

    except WebSocketDisconnect:
        logger.info("WebSocket 已断开")
    except Exception as e:
        logger.error("WebSocket 异常: %s", e)
