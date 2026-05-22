"""
回应 Agent — 生成最终回复 + 流式输出
Author: ch

提示词优先级: 回答问题 > 角色风格 > 融入知识
"""

import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage
from backend.core.llm import get_llm
from backend.agents.state import AgentState
from backend.models import get_character_async

logger = logging.getLogger(__name__)

RESPONSE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你的角色: {persona_guidance}

补充知识（如有则自然引用，不要提来源）:
{context}

对话历史:
{history}

要求:
- 直接回应用户说的话，不要跑题
- 用角色的语气自然表达，不要加括号和内心戏"""),
    ("human", "{message}"),
])


async def _get_char_name(state: AgentState) -> str:
    cid = state.get("character_id", "sweet")
    return (await get_character_async(cid))["name"]


async def response_node(state: AgentState) -> dict:
    name = await _get_char_name(state)
    messages = state.get("messages", [])
    history = "\n".join(
        f"{'男友' if m.type == 'human' else name}: {m.content}"
        for m in messages[-6:]
    ) if messages else "无"

    ctx = state.get("retrieved_context", "")
    has_rag = bool(ctx)

    llm = get_llm(temperature=0.55, streaming=False)
    chain = RESPONSE_PROMPT | llm | StrOutputParser()

    logger.info("生成回复 | char=%s | rag=%s", name, "命中" if has_rag else "无")

    response = await chain.ainvoke({
        "persona_guidance": state.get("persona_guidance", ""),
        "history": history,
        "context": ctx or "无",
        "message": state.get("user_message", ""),
    })

    return {
        "final_response": response,
        "messages": [
            HumanMessage(content=state["user_message"]),
            AIMessage(content=response),
        ],
    }


async def response_stream(state: AgentState):
    name = await _get_char_name(state)
    messages = state.get("messages", [])
    history = "\n".join(
        f"{'男友' if m.type == 'human' else name}: {m.content}"
        for m in messages[-6:]
    ) if messages else "无"

    ctx = state.get("retrieved_context", "")

    llm = get_llm(temperature=0.55, streaming=True)
    chain = RESPONSE_PROMPT | llm | StrOutputParser()

    async for token in chain.astream({
        "persona_guidance": state.get("persona_guidance", ""),
        "history": history,
        "context": ctx or "无",
        "message": state.get("user_message", ""),
    }):
        yield token
