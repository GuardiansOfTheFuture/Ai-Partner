"""
═══════════════════════════════════════════════════════════
AI 智能知识库助手 — FastAPI 应用入口
Author: ch
═══════════════════════════════════════════════════════════

启动:
  cd e:/python-pro/Multi-Agent
  uv run uvicorn backend.main:app --reload --port 8000

API 文档:
  ReDoc:  http://localhost:8000/redoc
  健康检查: http://localhost:8000/api/v1/health

架构层次（从上到下）:
  main.py (入口)
    → api/routes/*.py (路由层: 参数校验、错误处理)
      → services/*.py (服务层: 业务逻辑编排)
        → core/*.py (核心层: LLM、Embedding、向量库)
        → utils/*.py (工具层: 文件解析、分块)
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.router import api_router
from backend.config import settings
from backend.utils.logger import setup_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 生命周期管理

    asynccontextmanager:
      yield 之前 = 启动时执行
      yield 之后 = 关闭时执行
    """
    # ── 启动 ──
    setup_logging(logging.DEBUG if settings.debug else logging.INFO)
    logger.info("═" * 50)
    logger.info("AI 智能知识库助手 启动中...")
    logger.info("  LLM 模型: %s", settings.llm_model)
    logger.info("  Embedding: %s", settings.embedding_model)
    logger.info("  ChromaDB:  %s", settings.chroma_persist_dir)
    logger.info("  API 文档:  http://%s:%s/redoc", settings.host, settings.port)
    logger.info("═" * 50)

    yield

    # ── 关闭 ──
    logger.info("服务正在关闭...")


# ── 创建 FastAPI 应用 ──
app = FastAPI(
    title="AI 智能知识库助手",
    description="""
## 基于多 Agent 架构的 RAG 知识库问答系统

### 技术栈
- **后端**: FastAPI + LangChain + LangGraph
- **LLM**: 阿里云百炼 (通义千问)
- **向量库**: ChromaDB
- **前端**: 微信小程序 (Phase 5)

### 核心功能
1. 📄 多格式文档上传 (PDF/DOCX/TXT)
2. 🔍 语义检索 + RAG 问答
3. 📎 答案来源追溯
4. 🤖 多 Agent 协作 (Phase 3)
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS 中间件 ──
#   允许前端/小程序跨域访问
#   生产环境应限制 allow_origins 为具体域名
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 注册路由 ──
app.include_router(api_router)
