"""管理后台 API"""
import hashlib
import secrets
import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException, Header
from pydantic import BaseModel
from backend.services.document_service import process_document
from backend.core.vector_store import get_all_chunks, get_document_list, delete_by_doc_id

router = APIRouter(prefix="/api/v1/admin", tags=["管理后台"])

ADMIN_USER = "admin"
ADMIN_PASS = hashlib.sha256("admin123".encode()).hexdigest()
_tokens = set()
ALLOWED_EXT = {".pdf", ".docx", ".doc", ".txt", ".md", ".markdown"}


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


class DocumentResponse(BaseModel):
    document_id: str
    file_name: str
    file_type: str
    chunk_count: int
    status: str


@router.get("/dashboard")
async def dashboard(_auth=Header(None)):
    docs = get_document_list()
    return {
        "document_count": len(docs),
        "chunk_count": len(get_all_chunks()),
        "user_count": 1,
    }


@router.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...), _auth=Header(None)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail=f"不支持: {ext}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    try:
        return DocumentResponse(**process_document(tmp_path, file.filename))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.get("/documents")
async def list_docs(_auth=Header(None)):
    docs = get_document_list()
    return {"items": docs, "total": len(docs)}


@router.delete("/documents/{doc_id}")
async def delete_doc(doc_id: str, _auth=Header(None)):
    delete_by_doc_id(doc_id)
    return {"status": "deleted"}


@router.get("/documents/{doc_id}/chunks")
async def get_chunks(doc_id: str, _auth=Header(None)):
    chunks = get_all_chunks()
    doc_chunks = [
        {"content": c["content"], "meta": c["metadata"]}
        for c in chunks if c["metadata"].get("document_id") == doc_id
    ]
    return {"document_id": doc_id, "chunks": doc_chunks, "total": len(doc_chunks)}
