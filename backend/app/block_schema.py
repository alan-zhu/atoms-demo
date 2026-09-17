"""通用 Block Schema 定义 + 预置 presets。

一个 app_config 的通用形态:
{
  "meta": { "brand": "...", "accent": "violet", "version": 2 },
  "blocks": [
    {
      "id": "b1",
      "type": "heading",
      "props": { "text": "今天要完成的事", "size": "h1", "eyebrow": "TODAY'S FOCUS" }
    },
    {
      "id": "b2",
      "type": "task-list",
      "props": { "placeholder": "添加新任务" },
      "events": {
        "source": { "record_type": "task", "filter": {} },
        "handlers": {
          "task_create":  { "action": "upsert",  "record_type": "task",  "payload_fields": ["title"] },
          "task_update":  { "action": "update",  "record_type": "task",  "payload_fields": ["record_id", "status"] },
          "task_delete":  { "action": "delete",  "record_type": "task",  "payload_fields": ["record_id"] }
        }
      }
    },
    {
      "id": "b3",
      "type": "button",
      "props": { "label": "预约演示", "variant": "primary", "onClick": "openContactForm" }
    },
    {
      "id": "b4",
      "type": "feature-grid",
      "props": { "columns": 4, "items": [...] }
    }
  ]
}

目前支持的 block 类型 (按复杂度):
  - heading      : 标题 + 可选 eyebrow
  - text         : 描述文字
  - button       : 动作按钮 (primary / ghost / link)
  - task-list    : 待办清单 (完整 CRUD)
  - contact-form : 联系人表单 (提交 contact 记录)
  - pricing-grid : 定价网格 (静态)
  - event-hero   : 活动头部 (日期/标题)
  - session-list : 活动场次列表 (静态)
  - registration-form : 活动报名表单 (提交 registration 记录)
"""

from __future__ import annotations

import re
from typing import Any

# ─── helpers ────────────────────────────────────────────────

def _make_id() -> str:
    import secrets
    return secrets.token_urlsafe(6).replace("-", "x")


# ─── Block presets ───────────────────────────────────────────

def _heading(text: str, *, eyebrow: str | None = None, size: str = "h1") -> dict:
    return {"id": _make_id(), "type": "heading", "props": {"text": text, "size": size, **({"eyebrow": eyebrow} if eyebrow else {})}}


def _text(content: str) -> dict:
    return {"id": _make_id(), "type": "text", "props": {"content": content}}


def _button(label: str, *, variant: str = "primary", onClick: str | None = None) -> dict:
    b = {"id": _make_id(), "type": "button", "props": {"label": label, "variant": variant}}
    if onClick:
        b["props"]["onClick"] = onClick
    return b


def _contact_form() -> dict:
    return {
        "id": _make_id(),
        "type": "contact-form",
        "props": {"title": "预约产品演示", "successText": "收到你的信息"},
        "events": {
            "source": {"record_type": "contact", "filter": {}},
            "handlers": {
                "contact": {"action": "upsert", "record_type": "contact", "payload_fields": ["name", "email"]}
            },
        },
    }


def _feature_grid(items: list[dict]) -> dict:
    return {"id": _make_id(), "type": "feature-grid", "props": {"items": items, "columns": 4}}


def _pricing_grid(plans: list[dict]) -> dict:
    return {"id": _make_id(), "type": "pricing-grid", "props": {"plans": plans, "show": True}}


def _task_list(*, placeholder: str = "添加一个新任务…", compact: bool = False, showDue: bool = True, showProgress: bool = True) -> dict:
    return {
        "id": _make_id(),
        "type": "task-list",
        "props": {
            "placeholder": placeholder,
            "compact": compact,
            "showDue": showDue,
            "showProgress": showProgress,
            "statuses": [
                {"key": "todo", "label": "待处理", "color": "text-zinc-400 bg-zinc-400/10"},
                {"key": "in_progress", "label": "进行中", "color": "text-violet-300 bg-violet-400/10"},
                {"key": "done", "label": "已完成", "color": "text-emerald-300 bg-emerald-400/10"},
            ],
        },
        "events": {
            "source": {"record_type": "task", "filter": {}},
            "handlers": {
                "task_create": {
                    "action": "upsert",
                    "record_type": "task",
                    "payload_fields": ["title"],
                    "defaults": {"status": "todo"},
                },
                "task_update": {"action": "update", "record_type": "task", "payload_fields": ["record_id", "status"]},
                "task_delete": {"action": "delete", "record_type": "task", "payload_fields": ["record_id"]},
            },
        },
    }


def _section_nav(sections: list[str], *, active: int = 1) -> dict:
    return {
        "id": _make_id(),
        "type": "section-nav",
        "props": {"sections": sections, "active": active},
    }


def _event_hero(*, date: str, headline: str, eyebrow: str) -> dict:
    return {
        "id": _make_id(),
        "type": "event-hero",
        "props": {"date": date, "headline": headline, "eyebrow": eyebrow},
    }


def _session_list(sessions: list[str]) -> dict:
    return {"id": _make_id(), "type": "session-list", "props": {"sessions": sessions}}


def _registration_form(*, capacity: int) -> dict:
    return {
        "id": _make_id(),
        "type": "registration-form",
        "props": {"capacity": capacity, "title": "预留一个席位", "successText": "你已在名单中"},
        "events": {
            "source": {"record_type": "registration", "filter": {}},
            "handlers": {
                "registration": {"action": "upsert", "record_type": "registration", "payload_fields": ["name", "session"]}
            },
        },
    }


def _layout(*, variant: str = "centered", body_blocks: list[dict] | None = None, navItems: list[str] | None = None, headerBadge: str | None = None, brand: str = "") -> dict:
    """外层布局包裹器——定义 header/footer/nav 等框架。

    variant:
      - centered : 居中单列 (todo list)
      - kanban   : 侧边栏 + 主区 (项目工作台)
      - hero     : 顶部 hero 全宽 + 下方内容 (landing / event)
    """
    body_blocks = body_blocks or []
    # 把 brand 放到 navItems 的第一个位置（作为 header brand 展示）
    nav_list = [brand] + (navItems or []) if brand else (navItems or [])
    return {
        "id": _make_id(),
        "type": "layout",
        "props": {"variant": variant, "navItems": nav_list, "headerBadge": headerBadge or ""},
        "children": body_blocks,
    }


# ─── Config builders ─────────────────────────────────────────

def build_landing_config(prompt_focus: str, brand: str, accent: str) -> dict:
    """Landing = nav + hero + feature-grid + pricing-grid + contact-form + footer"""
    headline = "让每一个好想法，都有抵达市场的速度。"
    description = "从第一条灵感到完整体验，一个为高速团队打造的智能工作空间。"
    features = [
        {"icon": "⚡", "title": "极速启动", "desc": "从想法到上线，只需几分钟"},
        {"icon": "🎨", "title": "精美设计", "desc": "每个像素都经过精心打磨"},
        {"icon": "🔄", "title": "持续迭代", "desc": "对话式修改，实时预览效果"},
        {"icon": "📊", "title": "数据驱动", "desc": "内置分析，洞察每一个用户行为"},
    ]
    plans = [
        {"name": "Starter", "price": "¥0", "detail": "给刚开始的创作者"},
        {"name": "Growth", "price": "¥149", "detail": "给持续成长的团队", "featured": True},
        {"name": "Scale", "price": "定制", "detail": "给复杂业务与协作"},
    ]

    return {
        "meta": {"brand": brand, "accent": accent, "template": "landing"},
        "blocks": [
            _layout(variant="hero", brand=brand, body_blocks=[
                _heading(headline, eyebrow="BUILT FOR MOMENTUM"),
                _text(description),
                _button("开始体验", variant="primary", onClick="openContactForm"),
                _button("了解更多", variant="ghost"),
            ], navItems=["产品", "方案", "客户"], headerBadge="预约演示"),
            _feature_grid(features),
            _pricing_grid(plans),
            _contact_form(),
        ],
    }


def build_todo_config(prompt_focus: str, brand: str, accent: str) -> dict:
    """Todo list 简化版 — 居中布局，只有 heading + task-list"""
    return {
        "meta": {"brand": brand, "accent": accent, "template": "project", "style": "todo"},
        "blocks": [
            _layout(variant="centered", brand=brand, body_blocks=[
                _heading("今天要完成的事。", eyebrow="TODAY'S FOCUS"),
                _text("快速记下，逐一完成。一个简单直接的待办清单。"),
                _task_list(compact=True, showDue=False, showProgress=True),
            ]),
        ],
    }


def build_kanban_config(prompt_focus: str, brand: str, accent: str) -> dict:
    """Kanban 看板版 — 侧边栏 + 主区 heading + 任务列表（带 due 字段）"""
    sections = ["概览", "我的任务", "团队动态"]
    return {
        "meta": {"brand": brand, "accent": accent, "template": "project", "style": "kanban"},
        "blocks": [
            _layout(variant="kanban", brand=brand, navItems=sections, headerBadge="同步正常"),
            _section_nav(sections, active=1),
            _heading("把重要的工作，推进得更轻盈。", eyebrow="PROJECT OS", size="h2"),
            _text("一个聚焦节奏、协作与清晰优先级的项目空间。"),
            _task_list(compact=False, showDue=True, showProgress=False, placeholder="添加一个新任务…"),
        ],
    }


def build_event_config(prompt_focus: str, brand: str, accent: str) -> dict:
    """Event 报名页 — hero + session-list + registration-form"""
    return {
        "meta": {"brand": brand, "accent": accent, "template": "event", "capacity": 80, "date": "2026 年 10 月 24 日 · 上海"},
        "blocks": [
            _layout(variant="hero", brand=brand, body_blocks=[
                _event_hero(date="2026 年 10 月 24 日 · 上海", headline="留给真正想创造的人。", eyebrow="LIVE EXPERIENCE"),
            ]),
            _session_list(["上午 · 产品新范式", "下午 · AI 原生实践", "晚上 · Builder Night"]),
            _registration_form(capacity=80),
        ],
    }


# ─── Custom HTML (escape hatch for LLM) ────────────────────

def _custom_html(html_str: str, *, js: str | None = None, css: str | None = None) -> dict:
    """逃生舱 block — LLM 可以生成原始 HTML 字符串。

    注意：HTML 被直接注入，使用时必须经过内容安全审查。
    JS 字段会被加到页面全局 <script> 中，适合写事件绑定。
    """
    return {
        "id": _make_id(),
        "type": "custom-html",
        "props": {"html": html_str, **({"js": js} if js else {}), **({"css": css} if css else {})},
    }
