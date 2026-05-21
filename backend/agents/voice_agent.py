"""
语音 Agent — 决策是否出声 + TTS 合成
Author: ch

触发条件（满足任一即出声）:
  1. 用户明确要求: 关键词 "语音" "说给我听" 等
  2. 情绪极端: 开心 / 生气 / 撒娇

TTS 前清洗: 去掉括号内的内心戏，只读真正说出口的话
"""

import re
import logging
from backend.agents.state import AgentState
from backend.services.tts_service import text_to_speech

logger = logging.getLogger(__name__)

VOICE_KEYWORDS = ["语音", "说给我听", "用说的", "讲给我听", "读出来", "发语音", "出声", "speak"]
VOICE_EMOTIONS = {"开心", "生气", "撒娇"}

# 匹配半角和全角括号内的内容（内心戏，不应读出来）
_PAREN_RE = re.compile(r"[（(][^)）]*[)）]")


def _clean_for_tts(text: str) -> str:
    """去掉括号中的内心戏，只保留说出口的话"""
    return _PAREN_RE.sub("", text).strip()


async def voice_decision_node(state: AgentState) -> dict:
    msg = state.get("user_message", "")
    emotion = state.get("emotion", "")

    wants_voice = False
    if any(kw in msg for kw in VOICE_KEYWORDS):
        wants_voice = True
        logger.info("语音决策: 用户要求出声")
    elif emotion in VOICE_EMOTIONS:
        wants_voice = True
        logger.info("语音决策: 情绪触发 | emotion=%s", emotion)

    return {"wants_voice": wants_voice}


async def voice_generate_node(state: AgentState) -> dict:
    if not state.get("wants_voice"):
        return {"voice_url": ""}

    text = state.get("final_response", "")
    if not text:
        return {"voice_url": ""}

    # 去掉内心戏，只读真正说出口的话
    clean_text = _clean_for_tts(text)
    if not clean_text:
        return {"voice_url": ""}
    logger.debug("TTS 清洗 | before=%d after=%d", len(text), len(clean_text))

    try:
        filename = await text_to_speech(clean_text)
        return {"voice_url": f"/audio/{filename}"}
    except Exception as e:
        logger.error("语音生成失败: %s", e)
        return {"voice_url": ""}
