"""管理后台 API"""
import hashlib, secrets, os, tempfile, json
from fastapi import APIRouter, UploadFile, File, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy import select, func
from backend.db.database import async_session
from backend.models import UserModel, ConversationModel, MessageModel
from backend.services.document_service import process_document
from backend.core.vector_store import get_all_chunks, get_document_list, delete_by_doc_id
from backend.models.character import _FALLBACK

router = APIRouter(prefix="/api/v1/admin", tags=["管理后台"])

ADMIN_USER = "admin"
ADMIN_PASS = hashlib.sha256("admin123".encode()).hexdigest()
_tokens = set()
ALLOWED_EXT = {".pdf", ".docx", ".doc", ".txt", ".md", ".markdown"}


# ── 鉴权 ──
class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
async def login(req: LoginRequest):
    pwd = hashlib.sha256(req.password.encode()).hexdigest()
    if req.username != ADMIN_USER or pwd != ADMIN_PASS:
        raise HTTPException(status_code=401, detail="账号或密码错误")
    token = secrets.token_hex(32)
    _tokens.add(token)
    return {"token": token}


def _check(authorization: str = Header(None)):
    if not authorization or authorization.replace("Bearer ", "") not in _tokens:
        raise HTTPException(status_code=401)


# ── 仪表盘 ──
@router.get("/dashboard")
async def dashboard(_auth=Header(None)):
    async with async_session() as db:
        user_count = (await db.execute(select(func.count(UserModel.id)))).scalar()
        conv_count = (await db.execute(select(func.count(ConversationModel.id)))).scalar()
    docs = get_document_list()
    return {
        "document_count": len(docs),
        "chunk_count": len(get_all_chunks()),
        "user_count": user_count or 0,
        "conversation_count": conv_count or 0,
    }


# ── 文档管理（已有，不动） ──
class DocumentResponse(BaseModel):
    document_id: str; file_name: str; file_type: str; chunk_count: int; status: str


@router.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...), _auth=Header(None)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail=f"不支持: {ext}")
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        content = await file.read(); tmp.write(content); tmp_path = tmp.name
    try:
        return DocumentResponse(**process_document(tmp_path, file.filename))
    finally:
        if os.path.exists(tmp_path): os.unlink(tmp_path)


@router.get("/documents")
async def list_docs(_auth=Header(None), page: int = 1, page_size: int = 20):
    docs = get_document_list()
    total = len(docs)
    start = (page - 1) * page_size
    return {"items": docs[start:start+page_size], "total": total, "page": page, "page_size": page_size}


@router.delete("/documents/{doc_id}")
async def delete_doc(doc_id: str, _auth=Header(None)):
    delete_by_doc_id(doc_id)
    return {"status": "deleted"}


@router.get("/documents/{doc_id}/chunks")
async def get_chunks(doc_id: str, _auth=Header(None)):
    chunks = get_all_chunks()
    doc_chunks = [{"content": c["content"], "meta": c["metadata"]}
                  for c in chunks if c["metadata"].get("document_id") == doc_id]
    return {"document_id": doc_id, "chunks": doc_chunks, "total": len(doc_chunks)}


# ── 对话记录 ──
@router.get("/conversations")
async def list_conversations(_auth=Header(None), page: int = 1, page_size: int = 20):
    async with async_session() as db:
        total = (await db.execute(select(func.count(ConversationModel.id)))).scalar() or 0
        result = await db.execute(
            select(ConversationModel).order_by(ConversationModel.updated_at.desc())
            .offset((page - 1) * page_size).limit(page_size)
        )
        convs = result.scalars().all()
    items = []
    for c in convs:
        char = _FALLBACK.get(c.character_id, _FALLBACK["sweet"])
        items.append({
            "id": c.id, "character_name": char["name"], "character_avatar": char["avatar"],
            "title": c.title, "message_count": c.message_count,
            "created_at": c.created_at.isoformat() if c.created_at else "",
            "user_id": c.user_id or "",
        })
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/conversations/{conv_id}/messages")
async def get_conv_messages(conv_id: str, _auth=Header(None)):
    async with async_session() as db:
        result = await db.execute(
            select(MessageModel).where(MessageModel.conversation_id == conv_id)
            .order_by(MessageModel.created_at.asc())
        )
        msgs = result.scalars().all()
    return {
        "messages": [{"role": m.role, "content": m.content, "emotion": m.emotion,
                       "voice_url": m.voice_url, "created_at": m.created_at.isoformat()}
                      for m in msgs]
    }


# ── 用户管理 ──
@router.get("/users")
async def list_users(_auth=Header(None), page: int = 1, page_size: int = 20):
    async with async_session() as db:
        total = (await db.execute(select(func.count(UserModel.id)))).scalar() or 0
        result = await db.execute(
            select(UserModel).order_by(UserModel.created_at.desc())
            .offset((page - 1) * page_size).limit(page_size)
        )
        users = result.scalars().all()
    return {
        "items": [{"id": u.id, "openid": u.openid or "", "nickname": u.nickname or "未设置",
                    "is_active": u.is_active, "created_at": u.created_at.isoformat()}
                   for u in users],
        "total": total, "page": page, "page_size": page_size,
    }


class UserUpdate(BaseModel):
    is_active: bool


@router.put("/users/{user_id}")
async def update_user(user_id: str, data: UserUpdate, _auth=Header(None)):
    async with async_session() as db:
        user = await db.get(UserModel, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        user.is_active = data.is_active
        await db.commit()
    return {"status": "updated", "user_id": user_id, "is_active": data.is_active}


# ── 系统配置 ──
@router.get("/config")
async def get_config(_auth=Header(None)):
    # 从 DB 读取 + 内存兜底
    configs = {
        "llm_model": "qwen-plus",
        "embedding_model": "text-embedding-v4",
        "tts_model": "qwen3-tts-flash",
        "tts_voice": "Cherry",
        "max_upload_size_mb": "20",
        "chunk_size": "1000",
        "chunk_overlap": "200",
        "retrieve_top_k": "3",
    }
    try:
        from sqlalchemy import text as sqltxt
        async with async_session() as db:
            result = await db.execute(sqltxt("SELECT config_key, config_val FROM system_config"))
            for row in result:
                configs[row[0]] = row[1]
    except Exception as e:
        logger.warning("读取系统配置失败: %s", e)
    return {"configs": [{"key": k, "value": str(v)} for k, v in configs.items()]}


class ConfigUpdate(BaseModel):
    value: str


@router.put("/config/{key}")
async def update_config(key: str, data: ConfigUpdate, _auth=Header(None)):
    try:
        async with async_session() as db:
            from sqlalchemy import text as sqltxt
            await db.execute(
                sqltxt("INSERT INTO system_config (config_key, config_val) VALUES (:k, :v) "
                       "ON DUPLICATE KEY UPDATE config_val = :v"),
                {"k": key, "v": data.value}
            )
            await db.commit()
    except Exception:
        pass  # DB 不可用时静默
    return {"key": key, "value": data.value}
