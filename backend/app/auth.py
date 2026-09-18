"""JWT 鉴权 — 注册 / 登录 / token 解析依赖。"""

from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db
from .models import User, Visitor

# ─── 配置 ───────────────────────────────────────────────
SECRET_KEY = os.environ.get("AUTH_SECRET", secrets.token_urlsafe(48))
ALGORITHM = "HS256"
TOKEN_TTL_HOURS = 72  # 3 天


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(pw: str, hashed: str) -> bool:
    return bcrypt.checkpw(pw.encode("utf-8"), hashed.encode("utf-8"))


# ─── Token ────────────────────────────────────────────────

def create_token(user_id: str, visitor_id: str, email: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "visitor_id": visitor_id,
        "iat": now,
        "exp": now + timedelta(hours=TOKEN_TTL_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已过期，请重新登录")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的凭证")


# ─── FastAPI 依赖 ────────────────────────────────────────

def _extract_token(request: Request) -> Optional[str]:
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return None


def get_optional_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    """有 token 返回 User，没 token 返回 None（不强制登录）"""
    token = _extract_token(request)
    if not token:
        return None
    payload = decode_token(token)
    user = db.get(User, payload["sub"])
    return user


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """强制登录 — 用于需要身份的接口（后续可加）"""
    user = get_optional_user(request, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="请先登录")
    return user


def resolve_visitor(request: Request, db: Session) -> str:
    """优先级：JWT 里的 visitor_id > body 里的 visitor_id 字段 > 401

    这是关键的"向后兼容"设计：
    - 未登录用户继续传 visitor_id（现有前端逻辑不变）
    - 登录用户的 token 里自带 visitor_id，前端可以不传
    """
    token = _extract_token(request)
    if token:
        payload = decode_token(token)
        vid = payload.get("visitor_id")
        if vid and db.get(Visitor, vid):
            return vid
    # 回退：body 里拿 visitor_id
    return ""  # 调用方会检查空值
