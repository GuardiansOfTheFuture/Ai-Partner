"""
共享数据模型 — 服务层和路由层共用
Author: ch

设计意图:
  把 Pydantic 模型放在独立包中，服务层和路由层各自 import:
  - 服务函数返回模型实例 → 类型安全
  - 路由的 response_model 复用同一模型 → 避免重复定义
"""

from backend.models.document import DocumentResult
from backend.models.chat import ChatResult, SourceCitation

__all__ = ["DocumentResult", "ChatResult", "SourceCitation"]
