"""
知识检索 Agent — RAG 的 Retrieve 环节
Author: ch

流程:
  1. 接收用户消息
  2. embed_query → ChromaDB search → top-3 相关块
  3. 格式化为 LLM 可读的上下文文本
  4. 注入 state.retrieved_context → response_agent 会用
"""

import logging
from backend.core.vector_store import search
from backend.agents.state import AgentState

logger = logging.getLogger(__name__)


async def knowledge_retrieval_node(state: AgentState) -> dict:
    msg = state.get("user_message", "")
    if not msg:
        return {"retrieved_context": ""}

    # Step 1: 语义搜索（ChromaDB 内部自动 embed + HNSW 检索）
    results = search(msg, k=3)

    if not results:
        logger.debug("知识库无匹配 | query=%.50s", msg)
        return {"retrieved_context": ""}

    # Step 2: 提取纯文本内容（不附加来源标记，让 AI 自然融入）
    parts = [doc.page_content for doc, _ in results]

    context = "\n\n---\n\n".join(parts)

    # Step 3: 写入 state → response_agent 注入提示词
    logger.info("知识库命中 %d 条 | top1_score=%.3f | query=%.40s",
                len(results), results[0][1] if results else 0, msg)

    return {"retrieved_context": context}
