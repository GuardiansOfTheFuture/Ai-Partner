"""
聊天相关数据模型
Author: ch
"""

from pydantic import BaseModel, Field


class SourceCitation(BaseModel):
    """文档来源引用"""
    chunk_id: str = Field(..., description="文档块唯一 ID")
    document_name: str = Field(..., description="来源文件名")
    content_preview: str = Field(..., description="文档块内容预览（前150字）")
    score: float = Field(..., description="相似度分数")


class ChatResult(BaseModel):
    """RAG 问答结果 — 服务层和路由层共用"""
    answer: str = Field(..., description="LLM 生成的回答")
    sources: list[SourceCitation] = Field(default_factory=list, description="引用的文档来源")
