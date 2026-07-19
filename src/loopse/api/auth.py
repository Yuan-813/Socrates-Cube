"""Authentication routes — JWT + OTP.

支持四种登录方式：
1. 账号密码登录
2. 手机号 + OTP 验证码
3. 第三方登录（预留接口，返回重定向 URL）
4. 游客模式（直接以 guest-xxx 身份进入）

JWT Token 有效期 7 天，内含 sub（user_id）和 role_type。

响应格式：已迁移至 ApiResponse 统一包装（success/code/message/data）。
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import random
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ..schema.response import ok

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# ── JWT 配置 ──────────────────────────────────────────────────────────────
_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "socrates-cube-jwt-secret-2025")
_ALGORITHM = "HS256"
_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_EXPIRE_DAYS", "7"))

# ── OTP 内存存储（演示用；生产应替换为 Redis）────────────────────────────
# phone -> {code: str, expire_ts: float, verified: bool}
_otp_store: dict[str, dict] = {}
_OTP_TTL = 300  # 5 分钟


# ═══════════════════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════════════════

def _hash_password(password: str) -> str:
    """哈希密码（优先 bcrypt，无 passlib 时回退 SHA-256 + salt）。"""
    try:
        from passlib.context import CryptContext
        return CryptContext(schemes=["bcrypt"], deprecated="auto").hash(password)
    except Exception:
        salt = os.getenv("PWD_SALT", "socrates-cube-salt")
        return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def _verify_password(plain: str, hashed: str) -> bool:
    try:
        from passlib.context import CryptContext
        return CryptContext(schemes=["bcrypt"], deprecated="auto").verify(plain, hashed)
    except Exception:
        salt = os.getenv("PWD_SALT", "socrates-cube-salt")
        return hashlib.sha256(f"{salt}{plain}".encode()).hexdigest() == hashed


def _create_token(user_id: str, username: str, role_type: str = "student") -> str:
    """生成 JWT access token。python-jose 不可用时返回简易 token。"""
    payload: dict[str, Any] = {
        "sub": user_id,
        "username": username,
        "role_type": role_type,
        "iat": datetime.utcnow().isoformat(),
    }
    try:
        from jose import jwt as _jwt
        expire = datetime.utcnow() + timedelta(days=_TOKEN_EXPIRE_DAYS)
        payload["exp"] = expire
        return _jwt.encode(payload, _SECRET_KEY, algorithm=_ALGORITHM)
    except Exception:
        # 降级：base64 编码的 JSON（仅演示，不安全）
        import base64
        return base64.b64encode(json.dumps(payload).encode()).decode()


def decode_token(token: str) -> Optional[dict]:
    """解码 JWT token，返回 payload 或 None。"""
    try:
        from jose import jwt as _jwt, JWTError
        return _jwt.decode(token, _SECRET_KEY, algorithms=[_ALGORITHM])
    except Exception:
        try:
            import base64
            return json.loads(base64.b64decode(token).decode())
        except Exception:
            return None


# ═══════════════════════════════════════════════════════════════════════════
# 请求 / 响应模型
# ═══════════════════════════════════════════════════════════════════════════

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    email: Optional[str] = None
    role_type: str = Field(default="student")


class LoginRequest(BaseModel):
    username: str
    password: str


class PhoneSendOtpRequest(BaseModel):
    phone: str = Field(..., min_length=11, max_length=15)


class PhoneVerifyRequest(BaseModel):
    phone: str
    code: str = Field(..., min_length=4, max_length=8)


class UpdateProfileRequest(BaseModel):
    role_type: Optional[str] = None
    meta_json: Optional[dict] = None
    is_first_login: Optional[int] = None


class ChangePasswordRequest(BaseModel):
    user_id: str
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6, max_length=100)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str
    role_type: str
    is_first_login: int


# ═══════════════════════════════════════════════════════════════════════════
# 路由实现
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/register")
def register(req: RegisterRequest):
    """注册新用户。"""
    from ..db.repositories import get_db_session
    from ..db.models import User

    with get_db_session() as db:
        # 检查用户名重复
        if db.query(User).filter(User.username == req.username).first():
            raise HTTPException(status_code=409, detail="用户名已存在")
        # 检查邮箱重复
        if req.email and db.query(User).filter(User.email == req.email).first():
            raise HTTPException(status_code=409, detail="邮箱已被注册")

        user_id = str(uuid.uuid4())[:16]
        user = User(
            id=user_id,
            username=req.username,
            password_hash=_hash_password(req.password),
            email=req.email,
            role_type=req.role_type,
            is_first_login=1,
        )
        db.add(user)
        db.flush()
        db.refresh(user)

    logger.info("[Auth] 新用户注册 id=%s username=%s", user_id, req.username)
    token = _create_token(user_id, req.username, req.role_type)
    return ok(
        data=TokenResponse(
            access_token=token,
            user_id=user_id,
            username=req.username,
            role_type=req.role_type,
            is_first_login=1,
        ).model_dump(),
        message="注册成功",
    )


@router.post("/login")
def login(req: LoginRequest):
    """账号密码登录。"""
    from ..db.repositories import get_db_session
    from ..db.models import User

    with get_db_session() as db:
        user = db.query(User).filter(
            (User.username == req.username) | (User.email == req.username)
        ).first()
        if not user or not user.password_hash:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
            )
        if not _verify_password(req.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
            )
        is_first = user.is_first_login or 0
        # 标记非首次登录
        if user.is_first_login:
            user.is_first_login = 0
        role_type = user.role_type or "student"
        user_id = user.id
        username = user.username

    token = _create_token(user_id, username, role_type)
    logger.info("[Auth] 用户登录 id=%s username=%s", user_id, username)
    return ok(
        data=TokenResponse(
            access_token=token,
            user_id=user_id,
            username=username,
            role_type=role_type,
            is_first_login=is_first,
        ).model_dump(),
        message="登录成功",
    )


@router.post("/send-otp")
def send_otp(req: PhoneSendOtpRequest):
    """发送手机验证码（演示：直接返回验证码，生产需对接短信服务）。"""
    code = str(random.randint(100000, 999999))
    _otp_store[req.phone] = {"code": code, "expire_ts": time.time() + _OTP_TTL, "verified": False}
    logger.info("[Auth] OTP 已生成 phone=%s code=%s（演示模式：直接返回）", req.phone, code)
    # 演示模式：直接返回验证码；生产环境应调用短信 API 并隐藏 code
    return {"status": "sent", "phone": req.phone, "demo_code": code, "expire_seconds": _OTP_TTL}


@router.post("/verify-otp")
def verify_otp(req: PhoneVerifyRequest):
    """验证手机验证码并登录/注册。"""
    from ..db.repositories import get_db_session
    from ..db.models import User

    entry = _otp_store.get(req.phone)
    if not entry:
        raise HTTPException(status_code=400, detail="请先获取验证码")
    if time.time() > entry["expire_ts"]:
        del _otp_store[req.phone]
        raise HTTPException(status_code=400, detail="验证码已过期，请重新获取")
    if entry["code"] != req.code:
        raise HTTPException(status_code=400, detail="验证码错误")

    # 验证通过，查找或创建用户
    with get_db_session() as db:
        user = db.query(User).filter(User.phone == req.phone).first()
        is_first = 1
        if not user:
            user_id = f"phone-{req.phone[-4:]}-{str(uuid.uuid4())[:8]}"
            username = f"用户{req.phone[-4:]}"
            user = User(
                id=user_id, username=username, phone=req.phone,
                role_type="student", is_first_login=1,
            )
            db.add(user)
            db.flush()
            db.refresh(user)
        else:
            is_first = user.is_first_login or 0
            if user.is_first_login:
                user.is_first_login = 0
            user_id = user.id
            username = user.username

    del _otp_store[req.phone]
    token = _create_token(user_id, username, "student")
    return ok(
        data=TokenResponse(
            access_token=token, user_id=user_id, username=username,
            role_type="student", is_first_login=is_first,
        ).model_dump(),
        message="登录成功",
    )


@router.post("/guest")
def guest_login():
    """游客快速登录（无需注册，返回临时身份）。"""
    from ..db.repositories import UserRepository
    guest_id = f"guest-{str(uuid.uuid4())[:8]}"
    UserRepository.get_or_create(guest_id)
    token = _create_token(guest_id, f"游客_{guest_id[-4:]}", "student")
    return ok(
        data=TokenResponse(
            access_token=token, user_id=guest_id,
            username=f"游客_{guest_id[-4:]}", role_type="student", is_first_login=1,
        ).model_dump(),
        message="游客登录成功",
    )


@router.post("/update-profile")
def update_user_profile(user_id: str, req: UpdateProfileRequest):
    """更新用户角色和档案信息（登录后的引导步骤调用）。"""
    from ..db.repositories import get_db_session
    from ..db.models import User

    with get_db_session() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        if req.role_type is not None:
            user.role_type = req.role_type
        if req.meta_json is not None:
            user.meta_json = json.dumps(req.meta_json, ensure_ascii=False)
        if req.is_first_login is not None:
            user.is_first_login = req.is_first_login
        user.update_time = datetime.now()

    return {"status": "ok", "user_id": user_id}


@router.get("/me")
def get_me(token: str):
    """获取当前登录用户信息（通过 token 参数或 Authorization header）。"""
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效或过期的 token")
    return {
        "user_id": payload.get("sub"),
        "username": payload.get("username"),
        "role_type": payload.get("role_type", "student"),
    }


# ═════════════════════════════════════════════════════════════════════════
# 第三方 OAuth 登录（QQ / 微信）
# ═════════════════════════════════════════════════════════════════════════

_QQ_APP_ID = os.getenv("QQ_APP_ID", "")
_QQ_APP_KEY = os.getenv("QQ_APP_KEY", "")
_WECHAT_APP_ID = os.getenv("WECHAT_APP_ID", "")
_WECHAT_APP_SECRET = os.getenv("WECHAT_APP_SECRET", "")
_OAUTH_CALLBACK_BASE = os.getenv("OAUTH_CALLBACK_BASE", "http://localhost:8000")


@router.get("/oauth/qq")
def oauth_qq_redirect():
    """返回 QQ OAuth 授权跳转 URL。前端跳转到此 URL 可发起 QQ 登录。"""
    if not _QQ_APP_ID:
        demo_user_id = "qq_demo_user"
        demo_token = _create_token(demo_user_id, "QQ演示用户", "student")
        return {
            "redirect_url": None,
            "demo_token": demo_token,
            "demo_mode": True,
            "user": {
                "userId": demo_user_id,
                "username": "QQ演示用户",
                "roleType": "student",
                "isFirstLogin": 0,
            },
        }
    state = uuid.uuid4().hex
    callback = f"{_OAUTH_CALLBACK_BASE}/api/v1/auth/oauth/qq/callback"
    redirect_url = (
        f"https://graph.qq.com/oauth2.0/authorize"
        f"?response_type=code&client_id={_QQ_APP_ID}"
        f"&redirect_uri={callback}&scope=get_user_info&state={state}"
    )
    return {"redirect_url": redirect_url, "state": state}


@router.get("/oauth/qq/callback", response_model=TokenResponse)
def oauth_qq_callback(code: str, state: Optional[str] = None):
    """处理 QQ OAuth 授权回调，实现登录或注册。"""
    if not _QQ_APP_ID or not _QQ_APP_KEY:
        # 演示模式：忽略 OAuth，直接创建演示账号
        demo_id = f"qq-demo-{uuid.uuid4().hex[:8]}"
        from ..db.repositories import UserRepository
        UserRepository.get_or_create(demo_id)
        token = _create_token(demo_id, f"QQ用户_{demo_id[-4:]}", "student")
        return TokenResponse(access_token=token, user_id=demo_id, username=f"QQ用户_{demo_id[-4:]}",
                             role_type="student", is_first_login=1)

    try:
        import urllib.request
        import urllib.parse
        # Step 1: 交换 access_token
        callback = f"{_OAUTH_CALLBACK_BASE}/api/v1/auth/oauth/qq/callback"
        token_url = (
            f"https://graph.qq.com/oauth2.0/token?grant_type=authorization_code"
            f"&client_id={_QQ_APP_ID}&client_secret={_QQ_APP_KEY}"
            f"&code={code}&redirect_uri={urllib.parse.quote(callback)}"
        )
        with urllib.request.urlopen(token_url, timeout=10) as resp:
            token_resp = resp.read().decode()
        access_token = urllib.parse.parse_qs(token_resp).get("access_token", [None])[0]
        if not access_token:
            raise HTTPException(status_code=400, detail="QQ OAuth 获取 access_token 失败")

        # Step 2: 获取 OpenID
        openid_url = f"https://graph.qq.com/oauth2.0/me?access_token={access_token}"
        with urllib.request.urlopen(openid_url, timeout=10) as resp:
            openid_raw = resp.read().decode()
        import re as _re
        openid_match = _re.search(r'"openid"\s*:\s*"([^"]+)"', openid_raw)
        if not openid_match:
            raise HTTPException(status_code=400, detail="QQ OAuth 获取 OpenID 失败")
        openid = openid_match.group(1)

        # Step 3: 获取用户信息
        info_url = (
            f"https://graph.qq.com/user/get_user_info"
            f"?access_token={access_token}&oauth_consumer_key={_QQ_APP_ID}&openid={openid}"
        )
        with urllib.request.urlopen(info_url, timeout=10) as resp:
            import json as _json
            user_info = _json.loads(resp.read().decode())
        nickname = user_info.get("nickname", f"QQ用户")

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[Auth] QQ OAuth 异常: %s", exc)
        raise HTTPException(status_code=500, detail="QQ 登录失败，请稍后重试")

    # 创建或查找用户
    from ..db.repositories import get_db_session
    from ..db.models import User as _User
    qq_user_id = f"qq-{openid[:16]}"
    with get_db_session() as db:
        user = db.query(_User).filter(_User.id == qq_user_id).first()
        is_first = 1
        if not user:
            user = _User(id=qq_user_id, username=f"{nickname}_{qq_user_id[-4:]}",
                         role_type="student", is_first_login=1)
            db.add(user)
            db.flush()
        else:
            is_first = user.is_first_login or 0
            if user.is_first_login:
                user.is_first_login = 0
        actual_id, actual_username = user.id, user.username

    token = _create_token(actual_id, actual_username, "student")
    logger.info("[Auth] QQ OAuth 登录 id=%s nickname=%s", actual_id, nickname)
    return TokenResponse(access_token=token, user_id=actual_id, username=actual_username,
                         role_type="student", is_first_login=is_first)


@router.get("/oauth/wechat")
def oauth_wechat_redirect():
    """返回微信扫码登录 URL（需要微信公众号/开放平台资质）。"""
    if not _WECHAT_APP_ID:
        demo_user_id = "wechat_demo_user"
        demo_token = _create_token(demo_user_id, "微信演示用户", "student")
        return {
            "redirect_url": None,
            "demo_token": demo_token,
            "demo_mode": True,
            "user": {
                "userId": demo_user_id,
                "username": "微信演示用户",
                "roleType": "student",
                "isFirstLogin": 0,
            },
        }
    state = uuid.uuid4().hex
    callback = f"{_OAUTH_CALLBACK_BASE}/api/v1/auth/oauth/wechat/callback"
    import urllib.parse
    redirect_url = (
        f"https://open.weixin.qq.com/connect/qrconnect"
        f"?appid={_WECHAT_APP_ID}&redirect_uri={urllib.parse.quote(callback)}"
        f"&response_type=code&scope=snsapi_login&state={state}#wechat_redirect"
    )
    return {"redirect_url": redirect_url, "state": state}


@router.get("/oauth/wechat/callback", response_model=TokenResponse)
def oauth_wechat_callback(code: str, state: Optional[str] = None):
    """处理微信扫码登录回调。"""
    if not _WECHAT_APP_ID or not _WECHAT_APP_SECRET:
        demo_id = f"wx-demo-{uuid.uuid4().hex[:8]}"
        from ..db.repositories import UserRepository
        UserRepository.get_or_create(demo_id)
        token = _create_token(demo_id, f"微信用户_{demo_id[-4:]}", "student")
        return TokenResponse(access_token=token, user_id=demo_id, username=f"微信用户_{demo_id[-4:]}",
                             role_type="student", is_first_login=1)

    try:
        import urllib.request
        import json as _json
        token_url = (
            f"https://api.weixin.qq.com/sns/oauth2/access_token"
            f"?appid={_WECHAT_APP_ID}&secret={_WECHAT_APP_SECRET}"
            f"&code={code}&grant_type=authorization_code"
        )
        with urllib.request.urlopen(token_url, timeout=10) as resp:
            token_data = _json.loads(resp.read().decode())
        if "errcode" in token_data:
            raise HTTPException(status_code=400, detail=f"微信 OAuth 失败: {token_data.get('errmsg')}")
        access_token = token_data["access_token"]
        openid = token_data["openid"]

        # 获取用户信息
        info_url = (
            f"https://api.weixin.qq.com/sns/userinfo"
            f"?access_token={access_token}&openid={openid}&lang=zh_CN"
        )
        with urllib.request.urlopen(info_url, timeout=10) as resp:
            user_info = _json.loads(resp.read().decode())
        nickname = user_info.get("nickname", "微信用户")
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[Auth] 微信 OAuth 异常: %s", exc)
        raise HTTPException(status_code=500, detail="微信登录失败，请稍后重试")

    from ..db.repositories import get_db_session
    from ..db.models import User as _User
    wx_user_id = f"wx-{openid[:16]}"
    with get_db_session() as db:
        user = db.query(_User).filter(_User.id == wx_user_id).first()
        is_first = 1
        if not user:
            user = _User(id=wx_user_id, username=f"{nickname}_{wx_user_id[-4:]}",
                         role_type="student", is_first_login=1)
            db.add(user)
            db.flush()
        else:
            is_first = user.is_first_login or 0
            if user.is_first_login:
                user.is_first_login = 0
        actual_id, actual_username = user.id, user.username

    token = _create_token(actual_id, actual_username, "student")
    logger.info("[Auth] 微信 OAuth 登录 id=%s nickname=%s", actual_id, nickname)
    return TokenResponse(access_token=token, user_id=actual_id, username=actual_username,
                         role_type="student", is_first_login=is_first)


# ═════════════════════════════════════════════════════════════════════════════
# 个人中心扩展接口
# ═════════════════════════════════════════════════════════════════════════════

@router.get("/user/{user_id}")
def get_user_info(user_id: str):
    """获取用户完整信息（个人中心展示用）。"""
    from ..db.repositories import get_db_session
    from ..db.models import User

    with get_db_session() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="用户不存在")
        return {
            "user_id": user.id,
            "username": user.username,
            "email": user.email or "",
            "phone": user.phone or "",
            "role_type": user.role_type or "student",
            "onboarded": bool(user.onboarded),
            "create_time": user.create_time.strftime("%Y-%m-%d") if user.create_time else "",
            "meta_json": json.loads(user.meta_json) if user.meta_json else {},
        }


@router.post("/change-password")
def change_password(req: ChangePasswordRequest):
    """修改密码：验证旧密码后更新。"""
    from ..db.repositories import get_db_session
    from ..db.models import User
    from fastapi import HTTPException

    with get_db_session() as db:
        user = db.query(User).filter(User.id == req.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        if not user.password_hash:
            raise HTTPException(status_code=400, detail="该账号不支持密码修改（第三方登录账号）")
        if not _verify_password(req.old_password, user.password_hash):
            raise HTTPException(status_code=400, detail="旧密码错误")
        user.password_hash = _hash_password(req.new_password)
        user.update_time = datetime.now()

    logger.info("[Auth] 用户修改密码 id=%s", req.user_id)
    return {"status": "ok", "message": "密码修改成功"}
