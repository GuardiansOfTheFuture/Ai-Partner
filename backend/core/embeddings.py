"""
嵌入模型
Author: ch
"""
from langchain_community.embeddings import DashScopeEmbeddings
from backend.config import settings

_embedding = None


def get_embeddings():
    global _embedding
    if _embedding is None:
        _embedding = DashScopeEmbeddings(
            model=settings.embedding_model,
            dashscope_api_key=settings.dashscope_api_key,
        )
    return _embedding
