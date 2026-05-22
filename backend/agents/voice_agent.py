"""
语音 Agent — LLM 判断是否出声 + TTS 合成
Author: ch

决策方式: LLM(temperature=0.0) 判断用户是否想听语音
  - 避免关键词匹配的死板
  - temperature=0.0 保证同一句话判断一致

TTS: qwen3-tts-flash + Cherry 女声
"""

import re
import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from backend.core.llm import get_llm
from backend.agents.state import AgentState
from backend.services.tts_service import text_to_speech

logger = logging.getLogger(__name__)

# LLM 判断用户是否想听语音
VOICE_DECISION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """判断用户是否想让 AI 用语音回复他。

以下情况应该返回"是":
- 用户明确要求: "说给我听" "语音回复我" "用说的" "讲出来" "读给我听" "发语音" "出声"
- 用户暗示想听: "我想听你说" "能听到你的声音吗" "你说话给我听"
- 用户表达想听声音的意愿: "念给我听" "用声音告诉我"

以下情况返回"否":
- 普通聊天、提问、倾诉、撒娇、求助等，没有提到"说/讲/读/念/语音/声音/听"等关键词
- 用户说"我想你" "我爱你" "陪我聊聊" 等情感表达，但没有要语音

只返回一个字: "是" 或 "否"。"""),
    ("human", "用户说: {message}"),
])


_PAREN_RE = re.compile(r"[（(][^)）]*[)）]")


def _clean_for_tts(text: str) -> str:
    return _PAREN_RE.sub("", text).strip()


async def voice_decision_node(state: AgentState) -> dict:
    msg = state.get("user_message", "")

    llm = get_llm(temperature=0.0)
    chain = VOICE_DECISION_PROMPT | llm | StrOutputParser()

    result = (await chain.ainvoke({"message": msg})).strip()
    wants_voice = "是" in result

    if wants_voice:
        logger.info("语音决策: LLM 判断需要出声 | result=%s", result)

    return {"wants_voice": wants_voice}


async def voice_generate_node(state: AgentState) -> dict:
    if not state.get("wants_voice"):
        return {"voice_url": ""}

    text = state.get("final_response", "")
    if not text:
        return {"voice_url": ""}

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
