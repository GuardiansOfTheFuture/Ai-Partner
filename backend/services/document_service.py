"""
文档处理服务 — 编排文档摄入流水线
Author: ch

流水线（简化后）:
  原始文件 → LangChain Loader → Document 列表 → 分块 → 嵌入 → ChromaDB
  ↑                    ↑               ↑           ↑       ↑        ↑
  upload          load_document    [Document]   chunk   embed    add_docs

相比之前的手动解析版本:
  - parse_file() → load_document() (LangChain 原生 Loader)
  - 手动拼接文本 → Loader 直接返回 Document 对象
  - 自己解析页码 → PyPDFLoader 自动带 page metadata
"""

import logging
import uuid
import shutil
from pathlib import Path

from langchain_core.documents import Document

from backend.config import settings
from backend.models.document import DocumentResult
from backend.utils.file_parser import load_document
from backend.utils.chunkers import chunk_document
from backend.core.vector_store import add_documents, delete_by_document_id

logger = logging.getLogger(__name__)


def process_document(file_path: str, original_name: str) -> DocumentResult:
    """
    处理单个文档的完整流程

    Step 1: LangChain Loader 加载 → 返回 Document 列表
            PDF: 每页一个 Document（带 page metadata）
            DOCX/TXT/MD: 全文一个或多个 Document
    Step 2: 提取全文并分块 → chunk_document 会保留 metadata
    Step 3: 向量化+存储 → ChromaDB 自动调用 embedding
    Step 4: 归档原始文件

    Args:
        file_path: 上传的临时文件路径
        original_name: 用户看到的原始文件名

    Returns:
        DocumentResult — Pydantic 模型，路由层直接透传给前端
    """
    document_id = f"doc_{uuid.uuid4().hex[:12]}"
    file_type = Path(file_path).suffix.lower().lstrip(".")
    logger.info("开始处理文档 | id=%s | name=%s | type=%s",
                document_id, original_name, file_type)

    # Step 1: LangChain Loader 加载（替掉了之前手写的 parse_file）
    loaded_docs = load_document(file_path)
    full_text = "\n\n".join(doc.page_content for doc in loaded_docs if doc.page_content)

    if not full_text.strip():
        raise ValueError(f"文档内容为空: {original_name}")

    # Step 2: 分块（metadata 会传给每个 chunk）
    chunks = chunk_document(
        text=full_text,
        metadata={
            "document_id": document_id,
            "file_name": original_name,
            "file_type": file_type,
        },
    )

    # Step 3: 向量化 + 存储
    add_documents(chunks)

    # Step 4: 归档
    _save_uploaded_file(file_path, document_id, original_name)

    logger.info("文档处理完成 | id=%s | type=%s | chunks=%d | 原始段数=%d",
                document_id, file_type, len(chunks), len(loaded_docs))

    return DocumentResult(
        document_id=document_id,
        file_name=original_name,
        file_type=file_type,
        chunk_count=len(chunks),
    )


def _save_uploaded_file(src_path: str, document_id: str, original_name: str) -> str:
    """归档原始文件到持久化目录"""
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    dest = upload_dir / f"{document_id}_{original_name}"
    shutil.copy2(src_path, dest)
    logger.debug("原始文件已归档 | dest=%s", dest)
    return str(dest)


def delete_document(document_id: str) -> None:
    """删除文档: 清除向量 + 删除原始文件"""
    logger.info("删除文档 | id=%s", document_id)
    delete_by_document_id(document_id)

    upload_dir = Path(settings.upload_dir)
    deleted = 0
    for f in upload_dir.glob(f"{document_id}_*"):
        f.unlink()
        deleted += 1

    logger.info("文档删除完成 | id=%s | 清理文件数=%d", document_id, deleted)
