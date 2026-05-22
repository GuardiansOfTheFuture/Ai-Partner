"""
文档处理服务
Author: ch
"""

import logging
import uuid
import shutil
from pathlib import Path
from backend.config import settings
from backend.utils.file_parser import load_document
from backend.utils.chunkers import chunk_document
from backend.core.vector_store import add_chunks

logger = logging.getLogger(__name__)


def process_document(file_path: str, original_name: str) -> dict:
    doc_id = f"doc_{uuid.uuid4().hex[:12]}"
    file_type = Path(file_path).suffix.lower().lstrip(".")

    logger.info("处理文档 | id=%s | name=%s", doc_id, original_name)

    loaded = load_document(file_path)
    full_text = "\n\n".join(d.page_content for d in loaded if d.page_content)
    if not full_text.strip():
        raise ValueError("文档内容为空")

    chunks = chunk_document(full_text, metadata={
        "document_id": doc_id, "file_name": original_name, "file_type": file_type,
    })
    add_chunks(chunks)

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(file_path, upload_dir / f"{doc_id}_{original_name}")

    logger.info("处理完成 | id=%s | chunks=%d", doc_id, len(chunks))
    return {
        "document_id": doc_id, "file_name": original_name,
        "file_type": file_type, "chunk_count": len(chunks), "status": "ready",
    }
