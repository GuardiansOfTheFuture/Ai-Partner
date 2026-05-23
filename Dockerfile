FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.cloud.tencent.com/pypi/simple/

COPY backend/ ./backend/
COPY admin/ ./admin/
RUN mkdir -p data/audio data/uploads data/chroma_db

ENV HOST=0.0.0.0 PORT=80
EXPOSE 80

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "80"]
