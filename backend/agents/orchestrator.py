"""
LangGraph 编排器 — AI 女友多角色 + RAG
Author: ch

图谱:
  perception (情绪+意图) → memory (画像) → persona (人设)
  → knowledge (ChromaDB 检索) → response (生成回复)
  → voice_decision (LLM判断是否出声) → voice_generate (TTS) → END

RAG 流程:
  用户消息 → knowledge 节点 → ChromaDB.search → top-3 块
  → state.retrieved_context → response 提示词注入
  → LLM 基于知识库内容回答（知识库无匹配则正常聊天）
"""

from pydantic import BaseModel
from langgraph.graph import StateGraph, END
from backend.agents.state import AgentState
from backend.agents.perception_agent import perception_node
from backend.agents.memory_agent import memory_node
from backend.agents.persona_agent import persona_node
from backend.agents.knowledge_agent import knowledge_retrieval_node
from backend.agents.response_agent import response_node, response_stream
from backend.agents.voice_agent import voice_decision_node, voice_generate_node


class ChatResult(BaseModel):
    emotion: str
    intent: str
    thinking: str
    response: str
    voice_url: str = ""


class StreamEvent(BaseModel):
    type: str
    content: str = ""


def _should_voice(state: AgentState) -> str:
    return "voice_generate" if state.get("wants_voice") else END


def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("perception", perception_node)
    workflow.add_node("memory", memory_node)
    workflow.add_node("persona", persona_node)
    workflow.add_node("knowledge", knowledge_retrieval_node)
    workflow.add_node("response", response_node)
    workflow.add_node("voice_decision", voice_decision_node)
    workflow.add_node("voice_generate", voice_generate_node)

    workflow.set_entry_point("perception")
    workflow.add_edge("perception", "memory")
    workflow.add_edge("memory", "persona")
    workflow.add_edge("persona", "knowledge")
    workflow.add_edge("knowledge", "response")
    workflow.add_edge("response", "voice_decision")
    workflow.add_conditional_edges("voice_decision", _should_voice, {
        "voice_generate": "voice_generate",
        END: END,
    })
    workflow.add_edge("voice_generate", END)
    return workflow.compile()


graph = build_graph()


async def chat(user_message: str, chat_history: list | None = None, character_id: str = "sweet") -> ChatResult:
    state: AgentState = {
        "user_message": user_message, "character_id": character_id,
        "messages": list(chat_history) if chat_history else [],
        "emotion": "", "intent": "", "user_profile": "",
        "persona_guidance": "", "retrieved_context": "",
        "thinking": "", "final_response": "",
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


async def chat_stream(user_message: str, chat_history: list | None = None, character_id: str = "sweet"):
    state: AgentState = {
        "user_message": user_message, "character_id": character_id,
        "messages": list(chat_history) if chat_history else [],
        "emotion": "", "intent": "", "user_profile": "",
        "persona_guidance": "", "retrieved_context": "",
        "thinking": "", "final_response": "",
        "wants_voice": False, "voice_url": "",
    }

    state.update(await perception_node(state))
    state.update(await memory_node(state))
    state.update(await persona_node(state))
    state.update(await knowledge_retrieval_node(state))

    yield StreamEvent(type="thinking", content=_build_thinking(state))

    full_response = ""
    async for token in response_stream(state):
        full_response += token
        yield StreamEvent(type="token", content=token)

    state["final_response"] = full_response
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
    ctx = "，查了知识库" if state.get("retrieved_context") else ""
    return f"{m.get(e, '')}，{i.get(t, '')}{ctx}"
