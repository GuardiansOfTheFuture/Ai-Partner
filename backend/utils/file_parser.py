"""
文档加载器 — LangChain 原生 Loader 封装
Author: ch
"""

import logging
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader

logger = logging.getLogger(__name__)

_LOADER_MAP = {
    ".pdf": PyPDFLoader, ".docx": Docx2txtLoader, ".doc": Docx2txtLoader,
    ".txt": TextLoader, ".md": TextLoader, ".markdown": TextLoader,
}


def load_document(file_path: str) -> list:
    """加载文档 → LangChain Document 列表"""
    ext = Path(file_path).suffix.lower()
    loader_cls = _LOADER_MAP.get(ext)
    if not loader_cls:
        raise ValueError(f"不支持: {ext}")

    if loader_cls is TextLoader:
        loader = TextLoader(file_path, encoding="utf-8")
    else:
        loader = loader_cls(file_path)

    docs = loader.load()
    logger.info("加载完成 | %s | %d 段", Path(file_path).name, len(docs))
    return docs
