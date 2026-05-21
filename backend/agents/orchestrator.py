"""
LangGraph 编排器 — 小暖 AI
Author: ch

图谱: perception → memory → persona → response → voice_decision
        → (wants_voice ? voice_generate : END)
"""

import logging
from pydantic import BaseModel
from langgraph.graph import StateGraph, END
from backend.agents.state import AgentState
from backend.agents.perception_agent import perception_node
from backend.agents.memory_agent import memory_node
from backend.agents.persona_agent import persona_node
from backend.agents.response_agent import response_node, response_stream
from backend.agents.voice_agent import voice_decision_node, voice_generate_node

logger = logging.getLogger(__name__)


class ChatResult(BaseModel):
    emotion: str
    intent: str
    thinking: str
    response: str
    voice_url: str = ""


class StreamEvent(BaseModel):
    type: str       # "thinking" | "token" | "voice" | "done"
    content: str = ""


def _should_voice(state: AgentState) -> str:
    return "voice_generate" if state.get("wants_voice") else END


def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("perception", perception_node)
    workflow.add_node("memory", memory_node)
    workflow.add_node("persona", persona_node)
    workflow.add_node("response", response_node)
    workflow.add_node("voice_decision", voice_decision_node)
    workflow.add_node("voice_generate", voice_generate_node)

    workflow.set_entry_point("perception")
    workflow.add_edge("perception", "memory")
    workflow.add_edge("memory", "persona")
    workflow.add_edge("persona", "response")
    workflow.add_edge("response", "voice_decision")
    workflow.add_conditional_edges("voice_decision", _should_voice, {
        "voice_generate": "voice_generate",
        END: END,
    })
    workflow.add_edge("voice_generate", END)
    return workflow.compile()


graph = build_graph()


async def chat(user_message: str, chat_history: list | None = None) -> ChatResult:
    state: AgentState = {
        "user_message": user_message,
        "messages": list(chat_history) if chat_history else [],
        "emotion": "", "intent": "", "user_profile": "",
        "persona_guidance": "", "thinking": "", "final_response": "",
        "wants_voice": False, "voice_url": "",
    }
    result = await graph.ainvoke(state)
    return ChatResult(
        emotion=result.get("emotion", ""),
        intent=result.get("intent", ""),
        thinking=_build_thinking(result),
        response=result.get("final_response", ""),
        voice_url=result.get("voice_url", ""),
    )


async def chat_stream(user_message: str, chat_history: list | None = None):
    state: AgentState = {
        "user_message": user_message,
        "messages": list(chat_history) if chat_history else [],
        "emotion": "", "intent": "", "user_profile": "",
        "persona_guidance": "", "thinking": "", "final_response": "",
        "wants_voice": False, "voice_url": "",
    }

    # 感知 + 记忆 + 人设
    state.update(await perception_node(state))
    state.update(await memory_node(state))
    state.update(await persona_node(state))

    yield StreamEvent(type="thinking", content=_build_thinking(state))

    # 流式生成回复
    full_response = ""
    async for token in response_stream(state):
        full_response += token
        yield StreamEvent(type="token", content=token)

    state["final_response"] = full_response

    # 语音决策
    state.update(await voice_decision_node(state))
    if state.get("wants_voice"):
        state.update(await voice_generate_node(state))
        if state.get("voice_url"):
            yield StreamEvent(type="voice", content=state["voice_url"])

    yield StreamEvent(type="done")


def _build_thinking(state):
    m = {"开心":"他心情不错","难过":"需要我安慰","生气":"先别急着给建议","焦虑":"我要让他安心","平静":"日常聊天","撒娇":"他在撒娇呢"}
    i = {"倾诉":"他想要我倾听","求助":"需要我帮忙","闲聊":"想和我聊聊","撒娇":"想要我宠他","关心":"他在关心我"}
    e = state.get("emotion", "平静")
    t = state.get("intent", "闲聊")
    return f"{m.get(e, '')}，{i.get(t, '')}"
