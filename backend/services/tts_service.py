"""TTS 语音合成 — 百炼 Qwen3-TTS"""
import logging, uuid
from pathlib import Path
import httpx
import dashscope
from backend.config import settings

logger = logging.getLogger(__name__)

dashscope.base_http_api_url = "https://dashscope.aliyuncs.com/api/v1"
AUDIO_DIR = Path("data/audio")
MODEL = "qwen3-tts-flash"
VOICE = "Cherry"


async def text_to_speech(text: str) -> str:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex[:10]}.wav"
    filepath = AUDIO_DIR / filename

    logger.info("TTS | len=%d | model=%s", len(text), MODEL)

    response = dashscope.MultiModalConversation.call(
        model=MODEL,
        api_key=settings.dashscope_api_key,
        text=text,
        voice=VOICE,
        language_type="Chinese",
        stream=False,
    )

    audio_url = response.output.get("audio", {}).get("url", "")
    if not audio_url:
        raise RuntimeError(f"TTS 响应无音频: {response.output}")

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(audio_url)
        resp.raise_for_status()
        with open(filepath, "wb") as f:
            f.write(resp.content)

    logger.info("TTS 完成 | file=%s | size=%d", filename, len(resp.content))
    return filename
