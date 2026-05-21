"""
ChromaDB 向量数据库封装
Author: ch

核心知识点:
  1. ChromaDB 是开源的向量数据库:
     - 功能: 存储向量 + 元数据 + 相似度搜索
     - 定位: 向量数据库领域的 SQLite —— 轻量、嵌入式、零配置
     - 原理: 内部用 HNSW 近似最近邻算法，百万级向量毫秒级搜索

  2. Collection（集合）:
     类似 SQL 的 table，一个 collection 存储一类向量。
     本项目用一个 collection 存所有知识库文档块。

  3. 搜索原理:
     query → embedding 向量 → ChromaDB HNSW 索引 → 找到 Top-K 最近邻居 → 返回

  4. 相似度分数:
     ChromaDB 默认用余弦距离，分数范围取决于 embedding 模型。
     分数越高 = 语义越相关，但没有绝对阈值，需要实际测试。

  5. metadata 过滤:
     可以在搜索时过滤: {"document_id": "doc_123"} → 只搜某个文档
     这在多文档场景下非常有用: "只在这个合同里找"
"""

import logging
import os

from langchain_chroma import Chroma
from langchain_core.documents import Document

from backend.config import settings
from backend.core.embeddings import get_embeddings

logger = logging.getLogger(__name__)

# 集合名 — 整个项目的知识库存在同一个 collection 中
COLLECTION_NAME = "knowledge_base"


def _get_persist_dir() -> str:
    """确保持久化目录存在并返回路径"""
    persist_dir = settings.chroma_persist_dir
    os.makedirs(persist_dir, exist_ok=True)
    return persist_dir


def get_vector_store() -> Chroma:
    """
    获取 ChromaDB 实例

    关键参数:
      persist_directory → 数据保存到磁盘，重启不丢失
      embedding_function → 添加/搜索时自动调用，将文本转为向量

    注意: Chroma 内部会初始化 HNSW 索引，首次调用可能稍慢
    """
    embeddings = get_embeddings()
    persist_dir = _get_persist_dir()

    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,   # ← 自动向量化的关键
        persist_directory=persist_dir,   # ← 持久化的关键
    )


def add_documents(chunks: list[Document]) -> int:
    """
    批量添加文档块到向量库

    流程:
      1. Chroma 收到 Document 列表
      2. 对每个 doc.page_content 调用 embedding_function 转为向量
      3. 向量 + metadata 一起存入 HNSW 索引
      4. 索引自动更新，后续搜索立即可用

    Args:
        chunks: LangChain Document 列表
                每个 doc.page_content = 文本, doc.metadata = {
                    "document_id", "file_name", "file_type",
                    "chunk_id", "chunk_index"
                }

    Returns:
        成功添加的文档块数量

    Raises:
        ValueError: chunks 为空时抛出
    """
    if not chunks:
        raise ValueError("chunks 不能为空")

    store = get_vector_store()
    store.add_documents(chunks)
    logger.info("向量库写入完成 | 添加 %d 个文档块 | collection=%s",
                len(chunks), COLLECTION_NAME)
    return len(chunks)


def search(
    query: str,
    k: int = 5,
    filter_metadata: dict | None = None,
) -> list[tuple[Document, float]]:
    """
    语义相似度搜索 — RAG 流程的核心环节

    原理:
      query "退款政策是什么"
        ↓ embed_query()
      向量 [0.12, -0.34, 0.56, ...]
        ↓ ChromaDB HNSR 搜索
      [(Document("退款说明..."), 0.95),   ← 语义最相关
       (Document("退货流程..."), 0.88),   ← 次相关
       (Document("价格说明..."), 0.42),   ← 不太相关
       ...]

    Args:
        query: 用户自然语言问题
        k: 返回最相似的 k 个块，k 越大上下文越丰富但 LLM 处理越慢
        filter_metadata: 元数据过滤器
            例: {"document_id": "doc_abc"} → 只在指定文档内搜索

    Returns:
        [(Document, 相似度分数), ...]，按相似度降序排列
    """
    store = get_vector_store()

    logger.debug("向量搜索 | query=%.80s... | k=%d | filter=%s",
                 query, k, filter_metadata)

    results = store.similarity_search_with_score(
        query, k=k, filter=filter_metadata,
    )

    logger.info("向量搜索完成 | 命中 %d 个结果 | Top-1 分数=%.4f",
                len(results), results[0][1] if results else 0)

    return results


def delete_by_document_id(document_id: str) -> None:
    """
    按文档 ID 删除所有关联向量块

    原理: ChromaDB 的 delete(where={...}) 支持按 metadata 过滤删除
    删除后 HNSW 索引自动更新，后续搜索不再返回这些块
    """
    store = get_vector_store()
    store._collection.delete(where={"document_id": document_id})
    logger.info("向量删除完成 | document_id=%s", document_id)


def get_collection_stats() -> dict:
    """获取向量库统计信息"""
    store = get_vector_store()
    collection = store._collection
    return {
        "name": collection.name,
        "count": collection.count(),
    }
