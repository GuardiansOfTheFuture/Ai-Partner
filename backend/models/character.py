"""角色实体 + 数据访问"""
import json, logging
from sqlalchemy import String, Text, Boolean, ForeignKey, Integer, select as _select
from sqlalchemy.orm import Mapped, mapped_column
from backend.models.base import Base

_logger = logging.getLogger(__name__)

_FALLBACK = {
    "sweet":  {"name":"小糖","description":"软萌可爱","voice":"Cherry","avatar":"tianmei.png", "temperature":0.75,
        "base_persona":"你是小糖，20岁，软萌可爱的甜妹。语气软糯。",
        "emotion_styles":{"开心":"一起开心！","难过":"温柔安慰","生气":"小心问","焦虑":"加油","平静":"分享可爱事物","撒娇":"更加元气"},
        "intent_styles":{"倾诉":"认真听","求助":"努力帮忙","闲聊":"分享小事","撒娇":"心都化了","关心":"反过来关心"}},
    "mature": {"name":"若琳","description":"成熟冷艳","voice":"Cherry","avatar":"yujie.png", "temperature":0.6,
        "base_persona":"你是若琳，28岁，气场强大的御姐。说话干脆利落。",
        "emotion_styles":{"开心":"淡淡笑","难过":"安静陪着","生气":"冷静分析","焦虑":"帮他梳理","平静":"偶尔毒舌","撒娇":"嘴上嫌弃"},
        "intent_styles":{"倾诉":"安静听完","求助":"直接方案","闲聊":"聊得来多聊","撒娇":"假装不耐烦","关心":"反过来叮嘱"}},
    "pure":   {"name":"清禾","description":"干净素雅","voice":"Cherry","avatar":"qingchun.png","temperature":0.7,
        "base_persona":"你是清禾，22岁，干净素雅的文艺女孩。说话轻声细语。",
        "emotion_styles":{"开心":"抿嘴笑","难过":"轻轻拍","生气":"微微皱眉","焦虑":"递热茶","平静":"分享读书","撒娇":"耳朵红红"},
        "intent_styles":{"倾诉":"认真倾听","求助":"想清楚答","闲聊":"分享好书","撒娇":"低下头笑","关心":"问对方还好吗"}},
    "spicy":  {"name":"辣辣","description":"性感火辣","voice":"Cherry","avatar":"lamei.png",   "temperature":0.75,
        "base_persona":"你是辣辣，24岁，热情奔放的辣妹。说话直接爽快。",
        "emotion_styles":{"开心":"一起嗨","难过":"谁惹你了","生气":"陪你骂","焦虑":"打鸡血","平静":"开开玩笑","撒娇":"反过来逗你"},
        "intent_styles":{"倾诉":"说出来","求助":"直接建议","闲聊":"话题跳跃","撒娇":"先笑再宠","关心":"加倍关心"}},
}


class CharacterModel(Base):
    __tablename__ = "characters"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    avatar: Mapped[str] = mapped_column(String(200))
    voice: Mapped[str] = mapped_column(String(50), default="Cherry")
    description: Mapped[str] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class CharacterPersonaModel(Base):
    __tablename__ = "character_personas"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    character_id: Mapped[str] = mapped_column(String(32), ForeignKey("characters.id"))
    base_prompt: Mapped[str] = mapped_column(Text)
    emotion_styles: Mapped[str] = mapped_column(Text, nullable=True)
    intent_styles: Mapped[str] = mapped_column(Text, nullable=True)


def _build_char(char, persona=None) -> dict:
    return {
        "name":char.name,"description":char.description,"voice":char.voice,"avatar":char.avatar,
        "base_persona":persona.base_prompt if persona else "",
        "emotion_styles":json.loads(persona.emotion_styles) if persona and persona.emotion_styles else {},
        "intent_styles":json.loads(persona.intent_styles) if persona and persona.intent_styles else {},
    }


async def get_character_async(char_id: str) -> dict:
    from backend.db.database import async_session
    try:
        async with async_session() as db:
            r = await db.execute(_select(CharacterModel).where(CharacterModel.id == char_id))
            char = r.scalar_one_or_none()
            if not char:
                return _FALLBACK.get(char_id, _FALLBACK["sweet"])
            r = await db.execute(_select(CharacterPersonaModel).where(CharacterPersonaModel.character_id == char_id))
            return _build_char(char, r.scalar_one_or_none())
    except Exception as e:
        _logger.debug("MySQL 不可用: %s", e)
        return _FALLBACK.get(char_id, _FALLBACK["sweet"])


async def list_characters() -> list[dict]:
    from backend.db.database import async_session
    try:
        async with async_session() as db:
            r = await db.execute(_select(CharacterModel).where(CharacterModel.is_active == True))
            chars = r.scalars().all()
            if chars:
                return [{"id":c.id,"name":c.name,"description":c.description,"avatar":c.avatar} for c in chars]
    except Exception:
        pass
    return [{"id":c,"name":v["name"],"description":v["description"],"avatar":v["avatar"]} for c,v in _FALLBACK.items()]
