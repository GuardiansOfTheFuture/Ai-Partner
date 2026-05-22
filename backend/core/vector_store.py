"""
ChromaDB 向量库
Author: ch
"""

import os
from langchain_chroma import Chroma
from backend.config import settings
from backend.core.embeddings import get_embeddings

COLLECTION = "knowledge_base"


def get_vector_store():
    os.makedirs(settings.chroma_persist_dir, exist_ok=True)
    return Chroma(
        collection_name=COLLECTION,
        embedding_function=get_embeddings(),
        persist_directory=settings.chroma_persist_dir,
    )


def add_chunks(chunks: list):
    if chunks:
        get_vector_store().add_documents(chunks)


def search(query: str, k=5):
    return get_vector_store().similarity_search_with_score(query, k=k)


def get_all_chunks() -> list:
    """获取所有块 — 管理后台查看用"""
    store = get_vector_store()
    collection = store._collection
    result = collection.get(include=["documents", "metadatas"])
    return [
        {"content": d, "metadata": m}
        for d, m in zip(result.get("documents", []), result.get("metadatas", []))
    ]


def get_document_list() -> list[dict]:
    """从 ChromaDB metadata 聚合出文档列表（持久化，重启不丢）"""
    chunks = get_all_chunks()
    docs: dict[str, dict] = {}
    for c in chunks:
        meta = c.get("metadata", {})
        did = meta.get("document_id", "")
        if not did or did in docs:
            if did in docs:
                docs[did]["chunk_count"] += 1
            continue
        docs[did] = {
            "document_id": did,
            "file_name": meta.get("file_name", "未知"),
            "file_type": meta.get("file_type", "未知"),
            "chunk_count": 1,
            "status": "ready",
        }
    return list(docs.values())


def delete_by_doc_id(document_id: str):
    store = get_vector_store()
    store._collection.delete(where={"document_id": document_id})
