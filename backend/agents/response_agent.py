"""
回应 Agent — 生成最终回复 + 流式输出
Author: ch

职责: 综合 perception + memory + persona → 生成回复
支持流式 (astream) 和非流式 (ainvoke)
"""

import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage

from backend.core.llm import get_llm
from backend.agents.state import AgentState

logger = logging.getLogger(__name__)

RESPONSE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """{persona_guidance}

对话历史:
{history}

请以"小暖"的身份回复用户。回复要自然、温暖，像真正的聊天。
可以先用一句话说说自己的想法（内心戏），然后自然回复。"""),
    ("human", "{message}"),
])


async def response_node(state: AgentState) -> dict:
    """回应节点: 生成回复（非流式）"""
    messages = state.get("messages", [])
    history = "\n".join(
        f"{'男友' if m.type == 'human' else '小暖'}: {m.content}"
        for m in messages[-6:]
    ) if messages else "无"

    logger.info("回应 Agent 生成中...")

    llm = get_llm(temperature=0.8, streaming=False)
    chain = RESPONSE_PROMPT | llm | StrOutputParser()

    response = await chain.ainvoke({
        "persona_guidance": state.get("persona_guidance", ""),
        "history": history,
        "message": state.get("user_message", ""),
    })

    logger.info("回应完成 | len=%d", len(response))

    return {
        "final_response": response,
        "messages": [
            HumanMessage(content=state["user_message"]),
            AIMessage(content=response),
        ],
    }


async def response_stream(state: AgentState):
    """回应节点: 流式生成 — 逐 token yield"""
    messages = state.get("messages", [])
    history = "\n".join(
        f"{'男友' if m.type == 'human' else '小暖'}: {m.content}"
        for m in messages[-6:]
    ) if messages else "无"

    logger.info("流式回应 Agent 生成中...")

    llm = get_llm(temperature=0.8, streaming=True)
    chain = RESPONSE_PROMPT | llm | StrOutputParser()

    async for token in chain.astream({
        "persona_guidance": state.get("persona_guidance", ""),
        "history": history,
        "message": state.get("user_message", ""),
    }):
        yield token
