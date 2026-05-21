"""
RAG 聊天服务 — 检索增强生成的完整流程
Author: ch

核心知识点:
  1. RAG 是什么？
     Retrieval-Augmented Generation = 检索增强生成
     LLM 本身不知道你的文档内容（训练数据里没有）
     → 先检索出相关文档块 → 拼到提示词里 → LLM "看着"文档回答

  2. RAG 四步流程:
     Step 1 - Embed:   用户问题 → 嵌入模型 → 向量
     Step 2 - Retrieve: 向量 → ChromaDB → Top-K 相关文档块
     Step 3 - Context:  文档块 + 提示词模板 → LLM 可读的上下文
     Step 4 - Generate: LLM(系统提示词 + 上下文 + 用户问题) → 答案

  3. 为什么要有提示词模板？
     LLM 默认是"聊天模式"，不加约束它会自由发挥。
     提示词告诉 LLM: "你是一个知识库助手，只基于资料回答，不知道就说不知道"
     → 这大幅减少了幻觉（编造不存在的信息）

  4. 对话历史的作用:
     用户: "核心功能有哪些？"  → LLM 回答
     用户: "第二个是什么？"    → 如果没有历史，LLM 不知道"第二个"指什么
     → 把历史拼进去，LLM 理解了上下文

  5. Phase 3 预告:
     当前是单链 RAG (prompt | llm | parser)。
     Phase 3 用 LangGraph 拆成多 Agent:
       检索Agent → 重排序Agent → 问答Agent → 质检Agent
     每一步可以独立优化、重试、条件跳转。
"""

import logging
import time

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document

from backend.core.llm import get_llm
from backend.core.vector_store import search
from backend.models.chat import ChatResult, SourceCitation

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# 提示词模板 — RAG 的灵魂
#   {context}      会被替换为检索到的文档块
#   {chat_history} 会被替换为最近几轮对话
#   {question}     用户的当前问题
# ═══════════════════════════════════════════════════════════════

RAG_SYSTEM_PROMPT = """你是一个专业的知识库助手。请严格基于下方提供的【参考资料】回答问题。

要求：
1. 只使用参考资料中的信息，不要编造
2. 如果参考资料中没有相关信息，请直接说"资料中未找到相关信息"
3. 回答时注明信息来源（引用文档名称）
4. 用中文回答，简洁清晰

【参考资料】
{context}

【对话历史】
{chat_history}
"""

RAG_HUMAN_PROMPT = """【用户问题】
{question}"""


def _format_docs(docs_with_scores: list[tuple[Document, float]]) -> str:
    """
    将检索结果格式化为 LLM 可读的文本块

    LLM 不认 Document 对象，需要转成带标记的纯文本:
      [文档1 | 来源: 产品手册.pdf | 相关度: 0.95]
      退款政策: 用户购买后30天内可申请退款...

      ---

      [文档2 | 来源: FAQ.pdf | 相关度: 0.82]
      退货流程: ...

    相关度分数让 LLM 知道"这段信息有多可靠"
    """
    parts = []
    for i, (doc, score) in enumerate(docs_with_scores):
        source = doc.metadata.get("file_name", "未知")
        parts.append(
            f"[文档{i+1} | 来源: {source} | 相关度: {score:.3f}]\n{doc.page_content}"
        )
    return "\n\n---\n\n".join(parts)


def _format_chat_history(history: list[dict]) -> str:
    """
    格式化对话历史

    为什么只取最近 6 条？
      - LLM 上下文窗口有限，历史太长会挤占文档空间
      - 6 条（3 轮对话）足够理解上下文

    格式:
      用户: 核心功能有哪些？
      助手: 核心功能包括...
      用户: 第二个是什么？  ← LLM 可以推断"第二个"指"智能问答"
    """
    if not history:
        return "（无对话历史）"
    parts = []
    for msg in history[-6:]:
        role = "用户" if msg["role"] == "user" else "助手"
        parts.append(f"{role}: {msg['content']}")
    return "\n".join(parts)


async def chat(
    question: str,
    chat_history: list[dict] | None = None,
    top_k: int = 5,
) -> ChatResult:
    """
    执行 RAG 问答

    完整流程:
      question → search() → context → prompt → LLM → answer + sources

    Args:
        question: 用户问题
        chat_history: [{"role":"user","content":"..."}, {"role":"assistant","content":"..."}]
        top_k: 检索返回的文档块数量，越大上下文越丰富

    Returns:
        ChatResult(answer="基于文档的答案...", sources=[...])
    """
    chat_history = chat_history or []
    t_start = time.time()

    logger.info("RAG 问答开始 | question=%.100s... | top_k=%d", question, top_k)

    # ── Step 1-2: 检索 ──
    docs_with_scores = search(question, k=top_k)

    if not docs_with_scores:
        logger.warning("检索无结果 | question=%.100s...", question)
        return ChatResult(
            answer="知识库中没有找到相关信息。请先上传文档或换个问题试试。",
            sources=[],
        )

    # ── Step 3: 构建上下文 ──
    context = _format_docs(docs_with_scores)
    history_text = _format_chat_history(chat_history)

    # ── Step 4: LLM 生成 ──
    #   prompt | llm | StrOutputParser 是 LangChain LCEL 链式调用
    #   StrOutputParser 将 LLM 返回的 AIMessage 对象转为纯字符串
    llm = get_llm(temperature=0.0)
    prompt = ChatPromptTemplate.from_messages([
        ("system", RAG_SYSTEM_PROMPT),
        ("human", RAG_HUMAN_PROMPT),
    ])
    chain = prompt | llm | StrOutputParser()

    answer = await chain.ainvoke({
        "context": context,
        "chat_history": history_text,
        "question": question,
    })

    # ── 组装来源引用 ──
    sources = [
        SourceCitation(
            chunk_id=doc.metadata.get("chunk_id", ""),
            document_name=doc.metadata.get("file_name", "未知"),
            content_preview=doc.page_content[:150] + "...",
            score=round(score, 4),
        )
        for doc, score in docs_with_scores
    ]

    elapsed = time.time() - t_start
    logger.info("RAG 问答完成 | 耗时=%.2fs | 引用数=%d | 答案长度=%d",
                elapsed, len(sources), len(answer))

    return ChatResult(answer=answer, sources=sources)
