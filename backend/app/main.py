from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .auth import (create_token, decode_token, get_current_user, hash_password,
                   verify_password)
from .database import Base, engine, get_db
from .html_builder import generate_html
from .llm_generator import generate_app, get_llm_status
from .models import AppRecord, Message, Project, User, Version, Visitor
from .schemas import (AppEvent, IterateInput, LoginInput, ProjectCreate,
                      ProjectOut, PublishInput, RegisterInput, RestoreInput,
                      TokenOut, UserOut, VisitorInput, VisitorOut)
from .services import (alter_config, append_timeline_messages, build_config,
                       create_version, detect_template, is_todo_style,
                       make_share_token, seed_records, serialize_project,
                       timeline_for)

# ─── Load .env ────────────────────────────────────────────
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip('"').strip("'")
        import os
        os.environ.setdefault(key, val)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Path("data").mkdir(exist_ok=True)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Atoms Demo API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def project_query():
    return select(Project).options(selectinload(Project.messages), selectinload(Project.versions), selectinload(Project.records))


def owned_project(db: Session, project_id: str, visitor_id: str) -> Project:
    project = db.scalar(project_query().where(Project.id == project_id, Project.owner_id == visitor_id))
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在或无权访问")
    return project


def resolve_visitor(request: Request, db: Session, body_vid: str | None = None, query_vid: str | None = None) -> str:
    """解析 visitor_id：JWT > body > query。全都没给 → 401。"""
    # 1. JWT 优先
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        try:
            payload = decode_token(auth[7:].strip())
            vid = payload.get("visitor_id")
            if vid and db.get(Visitor, vid):
                return vid
        except HTTPException:
            pass  # token 无效或过期 → 回退

    # 2. body / query
    vid = body_vid or query_vid
    if vid and db.get(Visitor, vid):
        return vid

    raise HTTPException(status_code=401, detail="请先登录或刷新页面")


def resolve_visitor_strict(request: Request, db: Session) -> str:
    """强制 JWT（禁止 visitor_id 回退）。用于"必须登录"模式。"""
    auth = request.headers.get("Authorization", "")
    if not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    payload = decode_token(auth[7:].strip())
    vid = payload.get("visitor_id")
    if not vid or not db.get(Visitor, vid):
        raise HTTPException(status_code=401, detail="登录已失效，请重新登录")
    return vid


# ─── Auth Routes ──────────────────────────────────────────

@app.post("/api/auth/register", response_model=TokenOut)
def register(payload: RegisterInput, db: Session = Depends(get_db)):
    # email 唯一
    existing = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing:
        raise HTTPException(status_code=400, detail="这个邮箱已注册")

    user = User(email=payload.email.lower(), password_hash=hash_password(payload.password), name=payload.name)
    db.add(user)
    db.flush()

    # 关联（或复用）visitor
    if payload.visitor_id and db.get(Visitor, payload.visitor_id):
        visitor = db.get(Visitor, payload.visitor_id)
        visitor.user_id = user.id
    else:
        visitor = Visitor(user_id=user.id)
        db.add(visitor)
        db.flush()

    db.commit()
    db.refresh(user)
    db.refresh(visitor)

    token = create_token(user.id, visitor.id, user.email)
    return TokenOut(token=token, user=UserOut(id=user.id, email=user.email, name=user.name, created_at=user.created_at))


@app.post("/api/auth/login", response_model=TokenOut)
def login(payload: LoginInput, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="邮箱或密码不正确")

    # 确保有 visitor
    visitor = db.scalar(select(Visitor).where(Visitor.user_id == user.id))
    if not visitor:
        visitor = Visitor(user_id=user.id)
        db.add(visitor)
        db.commit()
        db.refresh(visitor)

    token = create_token(user.id, visitor.id, user.email)
    return TokenOut(token=token, user=UserOut(id=user.id, email=user.email, name=user.name, created_at=user.created_at))


@app.get("/api/auth/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return UserOut(id=user.id, email=user.email, name=user.name, created_at=user.created_at)


# ─── Legacy Visitor Route ────────────────────────────────


def public_project(db: Session, token: str) -> Project:
    project = db.scalar(project_query().where(Project.share_token == token, Project.is_published.is_(True)))
    if not project:
        raise HTTPException(status_code=404, detail="分享链接不存在或尚未发布")
    return project


@app.get("/api/health")
def health():
    status = get_llm_status()
    return {"status": "ok", **status}


@app.get("/api/llm-status")
def llm_status():
    """前端用来探测 AI 模式是否可用（有 API key）"""
    return get_llm_status()


@app.post("/api/visitors", response_model=VisitorOut)
def create_or_get_visitor(payload: VisitorInput, db: Session = Depends(get_db)):
    if payload.visitor_id and db.get(Visitor, payload.visitor_id):
        return {"id": payload.visitor_id}
    visitor = Visitor()
    db.add(visitor)
    db.commit()
    return {"id": visitor.id}


@app.get("/api/projects", response_model=list[ProjectOut])
def list_projects(request: Request, visitor_id: str | None = Query(default=None), db: Session = Depends(get_db)):
    vid = resolve_visitor_strict(request, db)
    projects = db.scalars(project_query().where(Project.owner_id == vid).order_by(Project.updated_at.desc())).unique().all()
    return [serialize_project(project) for project in projects]


@app.post("/api/projects", response_model=ProjectOut)
def create_project(payload: ProjectCreate, request: Request, db: Session = Depends(get_db)):
    vid = resolve_visitor_strict(request, db)

    if payload.llm_mode:
        # AI 生成路径 — 走 llm_generator
        config, timeline_msgs, used_real = generate_app(payload.prompt)
        timeline = [{"agent": "AI", "role": "系统", "content": m} for m in timeline_msgs]
        brand = config.get("meta", {}).get("brand", "AI 生成")
        has_task = any(b.get("type") == "task-list" for b in config.get("blocks", []))
        template_type = "project" if has_task else "landing"
    else:
        # 模板路径 — 原有逻辑
        template_type = detect_template(payload.prompt)
        config = build_config(template_type, payload.prompt)
        brand = config.get("meta", {}).get("brand", config.get("brand", "未命名"))
        timeline = timeline_for(template_type, is_iteration=False, prompt=payload.prompt, config=config)

    project = Project(owner_id=vid, name=brand, template_type=template_type, prompt=payload.prompt, app_config=config, share_token=make_share_token(), current_version=1)
    db.add(project)
    db.flush()
    db.add(Message(project_id=project.id, role="user", agent=None, content=payload.prompt))
    append_timeline_messages(db, project, timeline)
    seed_records(db, project)
    create_version(db, project, "首次生成可交互应用")
    db.commit()
    project = db.scalar(project_query().where(Project.id == project.id))
    return serialize_project(project, timeline=timeline)


@app.get("/api/projects/{project_id}", response_model=ProjectOut)
def get_project(project_id: str, request: Request, visitor_id: str | None = Query(default=None), db: Session = Depends(get_db)):
    vid = resolve_visitor_strict(request, db)
    return serialize_project(owned_project(db, project_id, vid))


@app.post("/api/projects/{project_id}/iterate", response_model=ProjectOut)
def iterate_project(project_id: str, payload: IterateInput, request: Request, db: Session = Depends(get_db)):
    vid = resolve_visitor_strict(request, db)
    project = owned_project(db, project_id, vid)
    project.app_config, summary = alter_config(project.app_config, payload.prompt)
    project.prompt = payload.prompt
    project.current_version += 1
    new_brand = project.app_config.get("meta", {}).get("brand") or project.app_config.get("brand")
    if new_brand:
        project.name = new_brand
    db.add(Message(project_id=project.id, role="user", agent=None, content=payload.prompt))
    timeline = timeline_for(project.template_type, is_iteration=True, prompt=payload.prompt, config=project.app_config)
    append_timeline_messages(db, project, timeline)
    create_version(db, project, summary)
    db.commit()
    project = db.scalar(project_query().where(Project.id == project.id))
    return serialize_project(project, timeline=timeline)


@app.post("/api/projects/{project_id}/restore", response_model=ProjectOut)
def restore_project(project_id: str, payload: RestoreInput, request: Request, db: Session = Depends(get_db)):
    vid = resolve_visitor_strict(request, db)
    project = owned_project(db, project_id, vid)
    version = db.scalar(select(Version).where(Version.project_id == project.id, Version.number == payload.version_number))
    if not version:
        raise HTTPException(status_code=404, detail="未找到这个版本")
    project.app_config = version.app_config
    project.prompt = version.prompt
    project.current_version += 1
    db.add(Message(project_id=project.id, role="agent", agent="系统", content=f"已恢复到版本 {version.number}：{version.summary}"))
    create_version(db, project, f"恢复自版本 {version.number}")
    db.commit()
    project = db.scalar(project_query().where(Project.id == project.id))
    return serialize_project(project)


@app.post("/api/projects/{project_id}/publish", response_model=ProjectOut)
def publish_project(project_id: str, payload: PublishInput, request: Request, db: Session = Depends(get_db)):
    vid = resolve_visitor_strict(request, db)
    project = owned_project(db, project_id, vid)
    project.is_published = True
    db.add(Message(project_id=project.id, role="agent", agent="Luna", content="发布检查完成，分享页面已准备就绪。"))
    db.commit()
    project = db.scalar(project_query().where(Project.id == project.id))
    return serialize_project(project)


@app.get("/api/share/{token}", response_model=ProjectOut)
def get_shared_project(token: str, db: Session = Depends(get_db)):
    return serialize_project(public_project(db, token), include_owner=False)


def _walk_blocks(blocks: list[dict]) -> list[dict]:
    """扁平遍历所有 blocks（递归 children）"""
    result: list[dict] = []
    for b in blocks:
        result.append(b)
        result.extend(_walk_blocks([c for c in b.get("children", [])]))
    return result


def _find_event_handler(config: dict, event_type: str) -> dict | None:
    """从 blocks 里找到匹配 event_type 的 handler 声明"""
    for block in _walk_blocks(config.get("blocks", [])):
        for handler_type, handler in block.get("events", {}).get("handlers", {}).items():
            if handler_type == event_type:
                return handler
    return None


def _handle_by_block_handlers(db: Session, project: Project, event: AppEvent) -> None:
    handler = _find_event_handler(project.app_config, event.type)
    if not handler:
        # 没有匹配 handler，回退 legacy（给老项目或未声明的事件）
        _handle_event_legacy(db, project, event)
        return

    action = handler.get("action", "upsert")
    record_type = handler["record_type"]
    payload_fields = handler.get("payload_fields", [])

    if action == "upsert":
        # 纯 upsert：直接存一条新记录（registration/contact/task_create 都这样）
        defaults = handler.get("defaults", {})
        filtered = {k: str(event.payload.get(k, ""))[:200] for k in payload_fields if k in event.payload}
        merged = {**defaults, **filtered}
        if not merged:
            raise HTTPException(status_code=422, detail="缺少必要字段")
        db.add(AppRecord(project_id=project.id, record_type=record_type, payload=merged))

    elif action in ("update", "delete"):
        rid = str(event.payload.get("record_id", ""))
        record = db.scalar(select(AppRecord).where(AppRecord.id == rid, AppRecord.project_id == project.id))
        if not record:
            raise HTTPException(status_code=404, detail="记录不存在")
        if action == "delete":
            db.delete(record)
        else:  # update
            update = dict(record.payload)
            for field in payload_fields:
                if field == "record_id":
                    continue
                if field in event.payload:
                    update[field] = str(event.payload[field])[:200]
            record.payload = update

    # 业务规则：registration 要检查 capacity
    if event.type == "registration":
        count = db.scalars(select(AppRecord).where(AppRecord.project_id == project.id, AppRecord.record_type == "registration")).all()
        capacity = project.app_config.get("meta", {}).get("capacity", 80) if "blocks" in project.app_config else project.app_config.get("capacity", 80)
        if len(count) >= int(capacity):
            raise HTTPException(status_code=409, detail="报名名额已满")

    db.commit()


def _handle_event_legacy(db: Session, project: Project, event: AppEvent) -> None:
    """旧 config 格式的 switch-case（给已存在 DB 里的老项目）"""
    payload = event.payload
    if event.type == "contact":
        name = str(payload.get("name", "访客"))[:80]
        email = str(payload.get("email", ""))[:120]
        if not email:
            raise HTTPException(status_code=422, detail="请填写邮箱")
        db.add(AppRecord(project_id=project.id, record_type="contact", payload={"name": name, "email": email}))
    elif event.type == "registration":
        name = str(payload.get("name", "访客"))[:80]
        session = str(payload.get("session", ""))[:120]
        if not session:
            raise HTTPException(status_code=422, detail="请选择场次")
        count = db.scalars(select(AppRecord).where(AppRecord.project_id == project.id, AppRecord.record_type == "registration")).all()
        if len(count) >= int(project.app_config.get("capacity", 80)):
            raise HTTPException(status_code=409, detail="报名名额已满")
        db.add(AppRecord(project_id=project.id, record_type="registration", payload={"name": name, "session": session}))
    elif event.type == "task_create":
        title = str(payload.get("title", "")).strip()[:140]
        if not title:
            raise HTTPException(status_code=422, detail="任务名称不能为空")
        db.add(AppRecord(project_id=project.id, record_type="task", payload={"title": title, "status": "todo", "due": "待安排"}))
    else:
        record_id = str(payload.get("record_id", ""))
        record = db.scalar(select(AppRecord).where(AppRecord.id == record_id, AppRecord.project_id == project.id))
        if not record or record.record_type != "task":
            raise HTTPException(status_code=404, detail="任务不存在")
        if event.type == "task_delete":
            db.delete(record)
        elif event.type == "task_update":
            update = dict(record.payload)
            if "status" in payload:
                update["status"] = str(payload["status"])
            if "title" in payload:
                update["title"] = str(payload["title"])[:140]
            record.payload = update
    db.commit()


def handle_event(db: Session, project: Project, event: AppEvent) -> None:
    if "blocks" in project.app_config:
        _handle_by_block_handlers(db, project, event)
    else:
        _handle_event_legacy(db, project, event)


@app.post("/api/projects/{project_id}/events", response_model=ProjectOut)
def owner_event(project_id: str, event: AppEvent, request: Request, visitor_id: str | None = Query(default=None), db: Session = Depends(get_db)):
    vid = resolve_visitor_strict(request, db)
    project = owned_project(db, project_id, vid)
    handle_event(db, project, event)
    project = db.scalar(project_query().where(Project.id == project.id))
    return serialize_project(project)


@app.post("/api/share/{token}/events", response_model=ProjectOut)
def shared_event(token: str, event: AppEvent, db: Session = Depends(get_db)):
    project = public_project(db, token)
    handle_event(db, project, event)
    project = db.scalar(project_query().where(Project.id == project.id))
    return serialize_project(project, include_owner=False)


@app.get("/api/projects/{project_id}/html")
def get_project_html(project_id: str, request: Request, visitor_id: str | None = Query(default=None), db: Session = Depends(get_db)):
    vid = resolve_visitor_strict(request, db)
    project = owned_project(db, project_id, vid)
    html_str = generate_html(project.template_type, project.app_config, share_token=project.share_token)
    return {"html": html_str}


@app.get("/api/share/{token}/page", response_class=HTMLResponse)
def serve_shared_page(token: str, db: Session = Depends(get_db)):
    project = public_project(db, token)
    return generate_html(project.template_type, project.app_config, share_token=token)
