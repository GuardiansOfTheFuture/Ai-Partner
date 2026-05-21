"""
文档管理 API
Author: ch

端点:
  POST   /api/v1/documents/upload  — 上传文档
  GET    /api/v1/documents         — 文档列表（Phase 2 完善）
  DELETE /api/v1/documents/{id}    — 删除文档

学习要点:
  1. UploadFile 是 FastAPI 的文件上传封装，底层是 Starlette 的 SpooledTemporaryFile
  2. tempfile.NamedTemporaryFile 创建临时文件用于解析
  3. try-finally 确保临时文件被清理，防止磁盘泄漏
  4. APIRouter 的 prefix 参数统一路由前缀，避免每个路由重复写
  5. 响应模型放在 backend/models 中共享，路由层不重复定义
"""

import logging
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel, Field

from backend.models.document import DocumentResult
from backend.services.document_service import process_document, delete_document
from backend.core.vector_store import get_collection_stats

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".md", ".markdown"}


# ── 路由特有的响应模型（只在路由层使用，不共享） ──

class ListDocumentsResponse(BaseModel):
    """GET / 响应 — 文档列表概览"""
    total_chunks: int = Field(..., description="向量库中的文档块总数")
    message: str = Field(default="", description="提示信息")


class DeleteResponse(BaseModel):
    """DELETE /{id} 响应 — 删除确认"""
    status: str = Field(default="deleted")
    document_id: str = Field(..., description="被删除的文档 ID")


# ── 路由 ──

@router.post("/upload", response_model=DocumentResult)
async def upload_document(file: UploadFile = File(...)):
    """
    上传文档并启动处理流程

    处理流程:
      上传文件 → 保存临时文件 → 解析 → 分块 → 向量化 → ChromaDB → 删除临时文件

    支持格式: PDF / DOCX / TXT / Markdown
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {ext}，支持: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    logger.info("收到上传请求 | file=%s", file.filename)

    with tempfile.NamedTemporaryFile(
        delete=False, suffix=ext, prefix="upload_",
    ) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    logger.debug("临时文件已创建 | path=%s | size=%d", tmp_path, len(content))

    try:
        return process_document(file_path=tmp_path, original_name=file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("文档处理异常 | file=%s", file.filename, exc_info=True)
        raise HTTPException(status_code=500, detail=f"文档处理失败: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
            logger.debug("临时文件已清理 | path=%s", tmp_path)


@router.get("", response_model=ListDocumentsResponse)
async def list_documents():
    """文档列表 — Phase 2 引入 MySQL 后将支持完整的分页列表"""
    stats = get_collection_stats()
    logger.debug("文档列表查询 | total_chunks=%d", stats["count"])
    return ListDocumentsResponse(
        total_chunks=stats["count"],
        message="文档列表功能将在 Phase 2 数据库模块中完善",
    )


@router.delete("/{document_id}", response_model=DeleteResponse)
async def remove_document(document_id: str):
    """删除文档 — 从 ChromaDB 清除向量块 + 删除原始文件"""
    logger.info("收到删除请求 | document_id=%s", document_id)
    try:
        delete_document(document_id)
        return DeleteResponse(document_id=document_id)
    except Exception as e:
        logger.error("删除文档异常 | id=%s", document_id, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
