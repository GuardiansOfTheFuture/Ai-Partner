"""
嵌入模型模块 — 将文本转为高维向量
Author: ch

核心知识点:
  1. 什么是 Embedding（嵌入）？
     把一段文字映射为一个固定长度的浮点数数组（向量），
     语义相近的文字 → 向量在空间中距离近 → 相似度搜索成为可能

  2. 百炼 text-embedding-v4:
     - 1024 维向量（每段文本用一个 1024 个 float 的数组表示）
     - API 调用，首次稍慢（网络），之后阿里云有缓存加速
     - 中文能力优秀，专为中文语义优化

  3. 本地 BGE 模型（备选）:
     - 无需网络、无 API 费用
     - 但需要下载模型文件（~33MB），首次加载慢
     - 适合离线开发或不想依赖云服务的场景

  4. 为什么 RAG 需要 Embedding？
     用户问题 "退款政策" 和文档块 "退货规则说明" 虽然字面上不同，
     但语义相近 → embedding 向量距离近 → 能被检索到
"""

import logging

from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.embeddings import Embeddings

from backend.config import settings

logger = logging.getLogger(__name__)


# ── 缓存 ──
#   避免每次调用 get_embeddings() 都创建新实例（特别是本地模型加载很慢）
_embedding_cache: dict[str, Embeddings] = {}


def get_embeddings(provider: str = "dashscope") -> Embeddings:
    """
    获取嵌入模型实例（带缓存）

    Args:
        provider: 嵌入提供者
            "dashscope" → 百炼云端（推荐，中文能力强，无需 GPU）
            "local"     → 本地 BGE 小模型（离线可用，不消耗 API 额度）

    Returns:
        LangChain Embeddings 实例，提供 embed_query() 和 embed_documents()

    使用示例:
        embeddings = get_embeddings()
        query_vec = embeddings.embed_query("退款政策")       # → [0.12, -0.34, ...]
        doc_vecs  = embeddings.embed_documents(["退货说明", "价格方案"])  # → [[...], [...]]
    """
    if provider in _embedding_cache:
        return _embedding_cache[provider]

    if provider == "dashscope":
        if not settings.dashscope_api_key:
            raise ValueError("DashScope API Key 未设置")

        logger.info("创建百炼嵌入模型 | model=%s", settings.embedding_model)
        embeddings = DashScopeEmbeddings(
            model=settings.embedding_model,
            dashscope_api_key=settings.dashscope_api_key,
        )

    elif provider == "local":
        # 延迟导入 — 不安装 sentence-transformers 也不影响主流程
        from langchain_community.embeddings import HuggingFaceEmbeddings

        logger.info("创建本地嵌入模型 | model=BAAI/bge-small-zh-v1.5 | device=cpu")
        embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-zh-v1.5",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},  # 归一化，相似度计算更准
        )

    else:
        raise ValueError(f"未知的嵌入提供者: {provider}，可选: dashscope / local")

    _embedding_cache[provider] = embeddings
    return embeddings
