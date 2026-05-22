"""
人设 Agent — 根据角色 ID 加载人设 + 情绪微调
Author: ch
"""

import logging
from backend.agents.state import AgentState
from backend.models import get_character_async

logger = logging.getLogger(__name__)


async def persona_node(state: AgentState) -> dict:
    """加载角色人设 + 情绪/意图风格微调"""
    character_id = state.get("character_id", "sweet")
    character = await get_character_async(character_id)

    emotion = state.get("emotion", "平静")
    intent = state.get("intent", "闲聊")
    profile = state.get("user_profile", "暂无")

    emotion_guide = character["emotion_styles"].get(emotion, "")
    intent_guide = character["intent_styles"].get(intent, "")

    guidance = f"""{character['base_persona']}

当前用户:
- 情绪: {emotion} → {emotion_guide}
- 意图: {intent} → {intent_guide}
- 画像: {profile}"""

    logger.info("人设: %s | emotion=%s intent=%s", character["name"], emotion, intent)

    return {"persona_guidance": guidance}
