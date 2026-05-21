"""
文档加载器 — LangChain 原生加载器的薄封装
Author: ch

LangChain 提供的加载器（我们不再手动解析）:
  格式    Loader                      返回
  ────    ──                          ──
  PDF     PyPDFLoader                每页一个 Document (metadata 含 page_number)
  DOCX    Docx2txtLoader             全文一个 Document
  TXT     TextLoader                 全文一个 Document
  MD      UnstructuredMarkdownLoader 全文一个 Document

为什么用 LangChain Loader 而不是自己写？
  1. 自动处理编码（UTF-8/GBK 自动检测）
  2. PDF 自动提取页码到 metadata
  3. 直接返回 LangChain Document 对象，无需手动转换
  4. 社区维护，bug 修复和新格式支持不用自己操心
"""

import logging
from pathlib import Path

from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
)

logger = logging.getLogger(__name__)

# 支持的格式 → 对应 Loader
#   Markdown (.md) 本质是纯文本，用 TextLoader 而不用 UnstructuredMarkdownLoader
#   后者依赖 heavy 的 `unstructured` 包（~500MB），没必要
_LOADER_MAP = {
    ".pdf":      PyPDFLoader,
    ".docx":     Docx2txtLoader,
    ".doc":      Docx2txtLoader,
    ".txt":      TextLoader,
    ".md":       TextLoader,
    ".markdown": TextLoader,
}


def load_document(file_path: str) -> list[Document]:
    """
    自动选择 Loader 加载文档 → 直接返回 LangChain Document 列表

    使用方式:
      docs = load_document("report.pdf")
      for doc in docs:
          print(doc.page_content)   # 文本内容
          print(doc.metadata)        # {"source": "...", "page": 1}

    Args:
        file_path: 文件路径

    Returns:
        LangChain Document 列表，每个 Document 已包含:
          - page_content: 文本内容
          - metadata: {"source": 文件路径, "page": 页码(pdf独有), ...}

    Raises:
        ValueError: 不支持的文件类型
    """
    ext = Path(file_path).suffix.lower()
    loader_cls = _LOADER_MAP.get(ext)

    if loader_cls is None:
        raise ValueError(
            f"不支持的文件类型: {ext}，"
            f"支持: {', '.join(_LOADER_MAP.keys())}"
        )

    logger.info("加载文档 | loader=%s | file=%s",
                loader_cls.__name__, Path(file_path).name)

    # TextLoader 在 Windows 下默认编码检测可能出错，显式指定 UTF-8
    if loader_cls is TextLoader:
        loader = TextLoader(file_path, encoding="utf-8")
    else:
        loader = loader_cls(file_path)
    docs = loader.load()

    logger.info("加载完成 | 文档段数=%d", len(docs))
    return docs
