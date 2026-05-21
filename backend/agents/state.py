"""
LangGraph 共享状态 — AgentState
Author: ch

AgentState 是所有 Agent 之间传递数据的唯一载体。
每个 Agent 节点读取 state，修改后返回新 state。
"""

from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
import operator


class AgentState(TypedDict):
    # ── 输入 ──
    user_message: str                    # 用户原始输入

    # ── 对话历史（自动累积） ──
    messages: Annotated[Sequence[BaseMessage], operator.add]

    # ── 感知层 ──
    emotion: str                         # 检测到的情绪: 开心/难过/生气/焦虑/平静
    intent: str                          # 用户意图:  倾诉/求助/闲聊/撒娇

    # ── 记忆层 ──
    user_profile: str                    # 用户画像摘要: 喜欢什么/重要日子/说过的事

    # ── 人设层 ──
    persona_guidance: str                # 人设指导: 本次应该用什么语气/风格

    # ── 输出 ──
    thinking: str                        # 思考过程
    final_response: str                  # 最终回复
    wants_voice: bool                    # 是否需要语音
    voice_url: str                       # 语音文件 URL
