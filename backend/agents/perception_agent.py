"""
感知 Agent — 分析用户意图和情绪
Author: ch

职责: 读用户消息 → 判断情绪 + 识别意图
输出: emotion, intent 写入 state
"""

import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from backend.core.llm import get_llm
from backend.agents.state import AgentState

logger = logging.getLogger(__name__)

PERCEPTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是情感分析专家。分析用户最后一条消息，返回 JSON 格式:

{{
  "emotion": "开心|难过|生气|焦虑|平静|撒娇",
  "intent": "倾诉|求助|闲聊|撒娇|关心"
}}

只返回 JSON，不要其他文字。"""),
    ("human", """对话历史:
{history}

用户最新消息: {message}

分析:"""),
])


async def perception_node(state: AgentState) -> dict:
    """感知节点: 分析用户情绪和意图"""
    msg = state.get("user_message", "")
    if not msg:
        return {"emotion": "平静", "intent": "闲聊"}

    # 取最近 4 条对话
    messages = state.get("messages", [])
    history = "\n".join(
        f"{'用户' if m.type == 'human' else 'AI'}: {m.content}"
        for m in messages[-4:]
    ) if messages else "无"

    logger.info("感知 Agent 分析中 | msg=%.50s...", msg)

    llm = get_llm(temperature=0.0)  # 分析任务要精确
    chain = PERCEPTION_PROMPT | llm | StrOutputParser()

    try:
        raw = await chain.ainvoke({"history": history, "message": msg})
        # 解析 JSON
        import json
        raw = raw.strip()
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw)
        emotion = result.get("emotion", "平静")
        intent = result.get("intent", "闲聊")
    except Exception:
        emotion, intent = "平静", "闲聊"

    logger.info("感知完成 | emotion=%s | intent=%s", emotion, intent)

    return {
        "emotion": emotion,
        "intent": intent,
    }
