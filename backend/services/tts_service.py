"""
TTS 语音合成服务 — 百炼 Qwen3-TTS
Author: ch

模型: qwen3-tts-flash (实时合成, ~1s 出结果)
音色: Cherry(女声), 更多音色见百炼文档
"""

import logging
import uuid
import httpx
from pathlib import Path
import dashscope
from backend.config import settings

logger = logging.getLogger(__name__)

AUDIO_DIR = Path("data/audio")
MODEL = "qwen3-tts-flash"
VOICE = "Cherry"


async def text_to_speech(text: str) -> str:
    """
    文字转语音 → 返回本地文件名

    使用百炼 Qwen3-TTS，调用 dashscope.MultiModalConversation
    """
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex[:10]}.wav"
    filepath = AUDIO_DIR / filename

    logger.info("TTS 合成 | len=%d | model=%s | voice=%s", len(text), MODEL, VOICE)

    # Qwen3-TTS 实时合成
    response = dashscope.MultiModalConversation.call(
        model=MODEL,
        api_key=settings.dashscope_api_key,
        text=text,
        voice=VOICE,
    )

    # 提取音频 URL
    try:
        audio_url = response.output["audio"]["url"]
    except (KeyError, TypeError):
        raise RuntimeError(f"TTS 响应异常: {response.output}")

    if not audio_url:
        raise RuntimeError("TTS 返回的音频 URL 为空")

    # 下载音频
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(audio_url)
        resp.raise_for_status()
        with open(filepath, "wb") as f:
            f.write(resp.content)

    logger.info("TTS 完成 | file=%s | size=%d", filename, len(resp.content))
    return filename
