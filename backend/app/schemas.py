from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field


class VisitorInput(BaseModel):
    visitor_id: str | None = None


class VisitorOut(BaseModel):
    id: str


# ─── Auth ─────────────────────────────────────────────────

class RegisterInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    name: str | None = Field(default=None, max_length=80)
    visitor_id: str | None = None


class LoginInput(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    name: str | None = None
    created_at: datetime


class TokenOut(BaseModel):
    token: str
    user: UserOut


# ─── Project ──────────────────────────────────────────────

class ProjectCreate(BaseModel):
    visitor_id: str | None = None  # 登录用户从 JWT 取
    prompt: str = Field(min_length=1, max_length=1600)
    llm_mode: bool = False


class IterateInput(BaseModel):
    visitor_id: str | None = None
    prompt: str = Field(min_length=1, max_length=1600)


class RestoreInput(BaseModel):
    visitor_id: str | None = None
    version_number: int = Field(ge=1)


class PublishInput(BaseModel):
    visitor_id: str | None = None


class AppEvent(BaseModel):
    type: Literal["contact", "task_create", "task_update", "task_delete", "registration"]
    payload: dict[str, Any] = Field(default_factory=dict)


class MessageOut(BaseModel):
    id: str
    role: str
    agent: str | None
    content: str
    created_at: datetime


class VersionOut(BaseModel):
    number: int
    summary: str
    created_at: datetime


class RecordOut(BaseModel):
    id: str
    record_type: str
    payload: dict[str, Any]
    created_at: datetime


class ProjectOut(BaseModel):
    id: str
    owner_id: str | None = None
    name: str
    template_type: str
    prompt: str
    app_config: dict[str, Any]
    is_published: bool
    share_token: str | None = None
    current_version: int
    created_at: datetime
    updated_at: datetime
    messages: list[MessageOut] = []
    versions: list[VersionOut] = []
    records: list[RecordOut] = []
    timeline: list[dict[str, str]] = []
