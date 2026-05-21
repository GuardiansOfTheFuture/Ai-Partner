"""
文档相关数据模型
Author: ch
"""

from pydantic import BaseModel, Field


class DocumentResult(BaseModel):
    """文档处理结果 — 服务层和路由层共用"""
    document_id: str = Field(..., description="文档唯一 ID")
    file_name: str = Field(..., description="原始文件名")
    file_type: str = Field(..., description="文件类型: pdf / docx / txt")
    chunk_count: int = Field(..., ge=0, description="切分后的文档块数量")
    status: str = Field(default="ready", description="处理状态")
