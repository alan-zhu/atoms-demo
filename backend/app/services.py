import copy
import re
import secrets
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from .block_schema import (build_event_config, build_kanban_config,
                           build_landing_config, build_todo_config)
from .models import AppRecord, Message, Project, Version, Visitor

AGENTS = [
    ("Emma", "产品经理"),
    ("Iris", "体验研究员"),
    ("Bob", "架构师"),
    ("Alex", "工程师"),
    ("Luna", "测试员"),
]


def make_share_token() -> str:
    return secrets.token_urlsafe(9).replace("-", "").replace("_", "")[:14]


def clean_title(prompt: str, fallback: str) -> str:
    compact = re.sub(r"[。！!，,；;].*", "", prompt).strip()
    compact = re.sub(r"^(帮我|请|我想|我要|让我)?\s*(做个|做|创建|生成|写|开发|设计|实现)?\s*(一个|一个)?\s*", "", compact)
    compact = re.sub(r"(网站|网页|应用|App|系统|工具|页面|平台)$", "", compact).strip()
    compact = re.sub(r"的$", "", compact).strip()
    return compact[:28] if len(compact) >= 3 else fallback


# ─── Template detection ────────────────────────────────────

_TODO_WORDS = {"todo", "to-do", "清单", "待办", "任务列表", "任务清单"}
_KANBAN_WORDS = {"看板", "项目管理", "project management", "项目面板", "dashboard", "项目工作台"}
_PROJECT_WORDS = _TODO_WORDS | _KANBAN_WORDS


def detect_template(prompt: str) -> str:
    source = prompt.lower()
    if any(word in source for word in _PROJECT_WORDS):
        return "project"
    if any(word in source for word in ["报名", "活动", "预约", "会议", "课程", "场次", "event"]):
        return "event"
    return "landing"


def is_todo_style(prompt: str) -> bool:
    """project 模板下，是否是简化的个人 todo 清单（vs 团队协作看板）"""
    source = prompt.lower()
    if not any(w in source for w in _TODO_WORDS):
        return False
    if any(w in source for w in _KANBAN_WORDS):
        return False
    return True


def _extract_focus(prompt: str) -> str:
    """从 prompt 提取一句话的核心焦点，用于让 Agent 消息更具体"""
    text = prompt.strip()
    # 去掉开头的常见祈使词 + 量词
    text = re.sub(r"^(帮我|请|我想|我要|让我)?\s*(做个|做|创建|生成|写|开发|设计|实现)?\s*(一个|一个)?\s*", "", text)
    text = re.sub(r"(的网站|的网页|的应用|的系统|的工具|的 App|的页面|的平台)$", "", text)
    text = re.sub(r"(网站|网页|应用|系统|工具|平台)$", "", text)
    text = re.sub(r"[。. ，,！!的]$", "", text).strip()
    if len(text) > 24:
        text = text[:24] + "…"
    return text if text else "这个应用"


def build_config(template_type: str, prompt: str) -> dict:
    accent = "violet"
    brand = clean_title(prompt, "待办清单" if template_type == "project" else "Lumen")
    focus = _extract_focus(prompt)

    if template_type == "event":
        return build_event_config(focus, brand, accent)

    if template_type == "project":
        if is_todo_style(prompt):
            return build_todo_config(focus, brand, accent)
        return build_kanban_config(focus, brand, accent)

    return build_landing_config(focus, brand, accent)


def extract_meta(config: dict) -> dict:
    """从新 blocks schema 或遗留旧 config 提取 meta 字段"""
    if "blocks" in config:
        return config.get("meta", {})
    return {k: config.get(k) for k in ("brand", "accent") if k in config}


def alter_config(config: dict, prompt: str) -> tuple[dict, str]:
    result = copy.deepcopy(config)
    source = prompt.lower()
    summary = "应用了这次修改"

    # 区分新旧 schema
    if "blocks" in result:
        meta = result.setdefault("meta", {})
    else:
        meta = result

    palette_words = {
        "蓝": "blue", "blue": "blue", "绿色": "emerald", "绿": "emerald",
        "橙": "orange", "orange": "orange", "紫": "violet", "violet": "violet",
    }
    for word, accent in palette_words.items():
        if word in source:
            meta["accent"] = accent
            summary = f"视觉主色 → {word} 色系"
            break

    if any(word in source for word in ["简洁", "极简", "留白"]):
        summary = "风格 → 更克制、留白"
    elif any(word in source for word in ["年轻", "活力", "酷", "cool"]):
        summary = "风格 → 更年轻有活力"
    elif any(word in source for word in ["专业", "商务", "企业"]):
        summary = "风格 → 专业商务感"

    return result, summary


def timeline_for(template_type: str, is_iteration: bool, prompt: str, config: dict) -> list[dict[str, str]]:
    focus = _extract_focus(prompt)
    brand = config.get("brand", "")
    headline = config.get("headline", "")

    # 按模板类型给 Bob/Alex 不同的技术细节（避免 landing 也说 TaskInput）
    if template_type == "project":
        bob_notes = [
            "数据模型确认了——任务只需要 id / title / status / createdAt，四字段足够。",
            "组件拆分为 TaskInput / TaskList / TaskItem 三个，状态由父组件统一管理。",
        ]
        alex_notes = [
            "💻 开始写代码。先搭骨架：input 框 + 列表容器 + 空状态提示。",
            "写好了 TaskItem 组件，支持勾选 / 编辑 / 删除三种交互。",
            "💾 页面已生成 {config_brand}，跑通了一遍增→改→删的主流程。",
        ]
    elif template_type == "event":
        bob_notes = [
            "数据模型：参与者只需 name / session / createdAt，capacity 控制在活动里。",
            "表单 + 场次选择 + 已报名计数，三块足够表达核心流程。",
        ]
        alex_notes = [
            "💻 写好了报名表单 + 场次选择器，提交后实时更新已报名数。",
            "💾 {config_brand} 报名页已生成，流程跑通。",
            "边界状态：名额满时后端会拒绝新报名，前端已做提示。",
        ]
    else:
        bob_notes = [
            "数据模型：不需要——这是个静态落地页，表单提交走后端接口。",
            "结构定了：导航 + hero + feature grid + pricing + footer，五块。",
        ]
        alex_notes = [
            "💻 写好了 hero 模块，表单用 modal 弹出。",
            "四个 feature grid + pricing 模块都已生成。",
            "💾 {config_brand} 已跑通，表单提交能收到数据。",
        ]

    # 每个 Agent 多条消息模板，按 hash 选一条保证稳定输出
    emma_new = [
        "📝 收到需求：「{focus}」。我先梳理核心交互和最小可用范围。",
        "针对「{focus}」，我定义了 3 个核心动作，先把路径跑通再扩展。",
        "功能范围已圈定，{config_brand} 的第一版聚焦把「{config_headline}」这句话落到实处。",
    ]
    iris_new = [
        "🎨 体验梳理：「{focus}」的界面节奏需要让用户第一眼就知道能做什么。",
        "我在想空状态怎么处理——第一次打开「{config_brand}」的时候，屏幕不应该是空的。",
        "视觉层级定下来了：最重要的操作放在正中间，次要功能收进角落。",
    ]
    luna_new = [
        "🧪 验收测试：我走了一遍完整流程，主路径没问题。",
        "边界状态测了一遍——空输入、重复提交、网络错误都处理好了。",
        "✅ 第一轮 QA 通过，「{config_brand}」可以交付。",
    ]

    emma_iter = [
        "📝 理解这次修改：「{focus}」。我先评估一下影响范围。",
        "这次改动主要集中在交互层，核心结构不需要动。",
    ]
    iris_iter = [
        "🎨 视觉调整：{focus} 这块我保持了整体风格，只改了细节。",
        "体验层面已对齐，改完之后页面还是连贯的。",
    ]
    bob_iter = [
        "数据结构不需要变更，现有字段能承载这次修改。",
        "确认了架构不变更，直接增量修改。",
    ]
    alex_iter = [
        "💻 代码改好了，跑通了一遍主流程。",
        "✅ 修改已应用到界面。",
    ]
    luna_iter = [
        "🧪 回归测试完成，没有引入新问题。",
        "✅ 验证通过，所有路径正常。",
    ]

    pool = {
        False: {  # new
            "Emma": emma_new,
            "Iris": iris_new,
            "Bob": bob_notes,
            "Alex": alex_notes,
            "Luna": luna_new,
        },
        True: {  # iteration
            "Emma": emma_iter,
            "Iris": iris_iter,
            "Bob": bob_iter,
            "Alex": alex_iter,
            "Luna": luna_iter,
        },
    }[is_iteration]

    steps = []
    for agent_name, role in AGENTS:
        msgs = pool[agent_name]
        idx = hash(prompt + agent_name + template_type) % len(msgs)
        content = msgs[idx].format(focus=focus, config_brand=brand, config_headline=headline)
        steps.append({"agent": agent_name, "role": role, "content": content})

    return steps


# ─── DB operations ────────────────────────────────────────

def append_timeline_messages(db: Session, project: Project, timeline: list[dict[str, str]]) -> None:
    for item in timeline:
        db.add(Message(project_id=project.id, role="agent", agent=item["agent"], content=item["content"]))


def create_version(db: Session, project: Project, summary: str) -> None:
    db.add(Version(
        project_id=project.id,
        number=project.current_version,
        summary=summary,
        prompt=project.prompt,
        app_config=copy.deepcopy(project.app_config),
    ))
    versions = db.scalars(
        select(Version).where(Version.project_id == project.id).order_by(Version.number.desc())
    ).all()
    for old in versions[3:]:
        db.delete(old)


def seed_records(db: Session, project: Project) -> None:
    if project.template_type != "project":
        return
    if project.app_config.get("style") == "todo":
        tasks = [
            ("今天要做的第一件事", "todo"),
            ("下午 3 点的会议", "todo"),
            ("写完周报", "done"),
        ]
        for title, status in tasks:
            db.add(AppRecord(
                project_id=project.id,
                record_type="task",
                payload={"title": title, "status": status},
            ))
    else:
        tasks = [
            ("梳理本周核心目标", "in_progress", "今天"),
            ("完善产品体验细节", "todo", "明天"),
            ("和团队同步发布节奏", "done", "已完成"),
        ]
        for title, status, due in tasks:
            db.add(AppRecord(
                project_id=project.id,
                record_type="task",
                payload={"title": title, "status": status, "due": due},
            ))


def serialize_project(project: Project, include_owner: bool = True,
                       timeline: list[dict[str, str]] | None = None) -> dict:
    return {
        "id": project.id,
        "owner_id": project.owner_id if include_owner else None,
        "name": project.name,
        "template_type": project.template_type,
        "prompt": project.prompt,
        "app_config": project.app_config,
        "is_published": project.is_published,
        "share_token": project.share_token if project.is_published or include_owner else None,
        "current_version": project.current_version,
        "created_at": project.created_at or datetime.utcnow(),
        "updated_at": project.updated_at or datetime.utcnow(),
        "messages": [
            {"id": m.id, "role": m.role, "agent": m.agent, "content": m.content, "created_at": m.created_at}
            for m in project.messages
        ],
        "versions": [
            {"number": v.number, "summary": v.summary, "created_at": v.created_at}
            for v in project.versions
        ],
        "records": [
            {"id": r.id, "record_type": r.record_type, "payload": r.payload, "created_at": r.created_at}
            for r in project.records
        ],
        "timeline": timeline or [],
    }
