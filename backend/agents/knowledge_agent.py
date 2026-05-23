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

    try:
        # Step 1: 语义搜索（ChromaDB 内部自动 embed + HNSW 检索）
        results = search(msg, k=3)
    except Exception as e:
        logger.error("知识库搜索异常: %s", e)
        return {"retrieved_context": ""}

    if not results:
        logger.debug("知识库无匹配 | query=%.50s", msg)
        return {"retrieved_context": ""}

    # Step 2: 提取纯文本内容，限制总长度防止超过 LLM token 限制
    parts = []
    total_len = 0
    for doc, _ in results:
        text = doc.page_content[:800]  # 每块最多 800 字
        parts.append(text)
        total_len += len(text)
        if total_len > 2400:  # 总共不超过 2400 字
            break

    context = "\n\n---\n\n".join(parts)

    # Step 3: 写入 state → response_agent 注入提示词
    logger.info("知识库命中 %d 条 | top1_score=%.3f | total_len=%d | query=%.40s",
                len(parts), results[0][1] if results else 0, total_len, msg)

    return {"retrieved_context": context}
