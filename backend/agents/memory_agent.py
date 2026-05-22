"""
记忆 Agent — 长期记忆 + 用户画像
Author: ch

职责: 从对话历史中提取关键信息 → 更新用户画像
输出: user_profile 写入 state

简化版: 不依赖外部数据库，每次从最近的对话历史中提取画像。
生产版: 存 MySQL，按 user_id 拉取累积画像。
"""

import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from backend.core.llm import get_llm
from backend.agents.state import AgentState

logger = logging.getLogger(__name__)

MEMORY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是记忆管理助手。从对话历史中提取用户的关键信息，生成简洁的用户画像。

提取维度:
- 称呼/绰号
- 喜好（食物、爱好、音乐等）
- 重要事件（生日、纪念日、近期大事）
- 性格特点
- 当前状态（心情、工作、健康等）

如果历史中暂无信息，返回 "新用户，暂无画像"。
用 2-3 句话描述，不要用列表。"""),
    ("human", "对话历史:\n{history}\n\n用户画像:"),
])


async def memory_node(state: AgentState) -> dict:
    """记忆节点: 提取用户画像"""
    messages = state.get("messages", [])
    if not messages:
        return {"user_profile": "新用户，暂无画像"}

    history = "\n".join(
        f"{'用户' if m.type == 'human' else 'AI'}: {m.content}"
        for m in messages[-10:]  # 最近 10 条
    )

    logger.info("记忆 Agent 提取画像中...")

    llm = get_llm(temperature=0.2)
    chain = MEMORY_PROMPT | llm | StrOutputParser()

    profile = await chain.ainvoke({"history": history})

    logger.info("记忆提取完成 | len=%d", len(profile))
    return {"user_profile": profile.strip()}
