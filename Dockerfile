FROM python:3.11-slim

WORKDIR /app

# 安装 uv
RUN pip install uv

# 依赖
COPY pyproject.toml uv.lock ./
RUN uv sync

# 源码
COPY backend/ ./backend/
COPY admin/ ./admin/
RUN mkdir -p data/audio data/uploads data/chroma_db

ENV HOST=0.0.0.0 PORT=80
EXPOSE 80

CMD ["uv", "run", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "80"]
