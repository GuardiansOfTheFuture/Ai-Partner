"""
微信登录 API
Author: ch

流程: wx.login() → code → 后端 → openid → token
开发阶段没有真实 AppID 时，用设备标识模拟登录
"""

import hashlib
import secrets
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.config import settings

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])

# 内存 token 存储（接 MySQL 后迁移到数据库）
_tokens: dict[str, str] = {}  # token → openid


class LoginRequest(BaseModel):
    code: str = Field(..., description="wx.login() 返回的临时 code")


class DevLoginRequest(BaseModel):
    """开发模式：不需要微信 code，用设备标识登录"""
    device_id: str = Field(default="dev-user-001")


class LoginResponse(BaseModel):
    token: str
    openid: str
    is_new_user: bool = False


@router.post("/login", response_model=LoginResponse)
async def wx_login(req: LoginRequest):
    """
    微信登录 — 用 code 换 openid

    生产环境: 调用微信 API
    开发环境: code 为空时走模拟登录
    """
    openid = ""

    if settings.debug and req.code.startswith("dev-"):
        # 开发模式：直接取 device_id 到 openid
        openid = req.code.replace("dev-", "")
    else:
        # 生产模式：调微信接口换 openid
        # TODO: 填入真实 AppID 和 AppSecret
        openid = await _code_to_openid(req.code)

    if not openid:
        raise HTTPException(status_code=400, detail="登录失败，无效的 code")

    # 检查是否新用户
    is_new = openid not in _tokens.values()

    # 生成 token
    token = secrets.token_hex(32)
    _tokens[token] = openid

    return LoginResponse(token=token, openid=openid, is_new_user=is_new)


def verify_token(token: str) -> bool:
    """校验 token 是否有效"""
    return token in _tokens


@router.post("/dev-login", response_model=LoginResponse)
async def dev_login(req: DevLoginRequest):
    """开发模式登录 — 不经过微信，直接用设备 ID"""
    openid = f"dev_{req.device_id}"
    is_new = openid not in _tokens.values()
    token = secrets.token_hex(32)
    _tokens[token] = openid
    return LoginResponse(token=token, openid=openid, is_new_user=is_new)


async def _code_to_openid(code: str) -> str:
    """调微信 jscode2session 接口换 openid"""
    # TODO: 替换为真实 AppID 和 AppSecret
    appid = settings.wx_appid or "wx0000000000000000"
    secret = settings.wx_secret or "00000000000000000000000000000000"

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.weixin.qq.com/sns/jscode2session",
            params={
                "appid": appid,
                "secret": secret,
                "js_code": code,
                "grant_type": "authorization_code",
            },
        )
        data = resp.json()
        return data.get("openid", "")
