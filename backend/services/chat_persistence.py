"""
对话持久化服务
Author: ch
"""

import uuid
import logging
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import UserModel, ConversationModel, MessageModel
from backend.models import get_character_async

logger = logging.getLogger(__name__)


async def ensure_user(openid: str, db: AsyncSession) -> UserModel:
    """确保用户存在，不存在则创建"""
    result = await db.execute(select(UserModel).where(UserModel.openid == openid))
    user = result.scalar_one_or_none()
    if not user:
        user = UserModel(id=f"usr_{uuid.uuid4().hex[:12]}", openid=openid)
        db.add(user)
        await db.commit()
    return user


async def create_conversation(user_id: str, character_id: str, db: AsyncSession) -> ConversationModel:
    conv = ConversationModel(
        id=f"conv_{uuid.uuid4().hex[:12]}",
        user_id=user_id, character_id=character_id,
    )
    db.add(conv)
    await db.commit()
    return conv


async def save_message(
    conv_id: str, role: str, content: str,
    emotion: str = None, voice_url: str = None, db: AsyncSession = None,
):
    """保存一条消息并更新对话计数"""
    msg = MessageModel(
        conversation_id=conv_id, role=role, content=content,
        emotion=emotion, has_voice=bool(voice_url), voice_url=voice_url,
    )
    db.add(msg)

    conv = await db.get(ConversationModel, conv_id)
    if conv:
        conv.message_count = (conv.message_count or 0) + 1

    await db.commit()


async def list_conversations(user_id: str, db: AsyncSession) -> list[dict]:
    result = await db.execute(
        select(ConversationModel)
        .where(ConversationModel.user_id == user_id)
        .order_by(ConversationModel.updated_at.desc())
    )
    convs = result.scalars().all()
    items = []
    for c in convs:
        char = await get_character_async(c.character_id)
        items.append({
            "id": c.id, "character_id": c.character_id,
            "character_name": char["name"],
            "character_avatar": char["avatar"],
            "title": c.title, "message_count": c.message_count,
            "created_at": c.created_at.isoformat() if c.created_at else "",
        })
    return items


async def get_messages(conv_id: str, db: AsyncSession) -> list[dict]:
    result = await db.execute(
        select(MessageModel)
        .where(MessageModel.conversation_id == conv_id)
        .order_by(MessageModel.created_at.asc())
    )
    msgs = result.scalars().all()
    return [
        {"role": m.role, "content": m.content,
         "emotion": m.emotion, "voice_url": m.voice_url}
        for m in msgs
    ]
