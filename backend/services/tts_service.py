"""TTS 语音合成 — CosyVoice v2 SDK"""
import logging, uuid, asyncio
from pathlib import Path
import dashscope
from dashscope.audio.tts_v2 import SpeechSynthesizer, AudioFormat
from backend.config import settings

logger = logging.getLogger(__name__)

# 全局初始化
dashscope.api_key = settings.dashscope_api_key
dashscope.base_websocket_api_url = "wss://dashscope.aliyuncs.com/api-ws/v1/inference"

AUDIO_DIR = Path("data/audio")
DEFAULT_MODEL = "cosyvoice-v3-flash"
DEFAULT_VOICE = "longxiaochun"


async def text_to_speech(text: str, voice: str = None, model: str = None) -> str:
    """
    文字转语音

    Args:
        text: 待合成文本
        voice: 音色名(系统音色或复刻音色ID)，默认 longxiaochun
        model: 模型名，默认 cosyvoice-v3-flash（复刻音色需用 cosyvoice-v3.5-plus）
    """
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex[:10]}.mp3"
    filepath = AUDIO_DIR / filename

    voice = voice or DEFAULT_VOICE
    model = model or DEFAULT_MODEL

    logger.info("TTS | len=%d | model=%s | voice=%.20s", len(text), model, voice)

    audio = await asyncio.to_thread(_synthesize, text, model, voice)

    with open(filepath, "wb") as f:
        f.write(audio)

    logger.info("TTS 完成 | file=%s | size=%d", filename, len(audio))
    return filename


def _synthesize(text: str, model: str, voice: str) -> bytes:
    synthesizer = SpeechSynthesizer(
        model=model,
        voice=voice,
        format=AudioFormat.MP3_22050HZ_MONO_256KBPS,
    )
    return synthesizer.call(text)
