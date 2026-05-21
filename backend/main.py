"""
小暖 AI 女友 — FastAPI 入口
启动: uv run uvicorn backend.main:app --reload --port 8000
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.api.router import api_router
from backend.config import settings
from backend.utils.logger import setup_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(logging.DEBUG if settings.debug else logging.INFO)
    # 确保运行时目录存在
    from pathlib import Path
    Path("data/audio").mkdir(parents=True, exist_ok=True)
    logger.info("小暖 AI 女友 启动中...")
    logger.info("  LLM: %s", settings.llm_model)
    logger.info("  http://%s:%s/redoc", settings.host, settings.port)
    yield
    logger.info("小暖已休眠")


app = FastAPI(
    title="小暖 AI 女友",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.mount("/audio", StaticFiles(directory="data/audio"), name="audio")
app.include_router(api_router)
