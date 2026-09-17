"""LLM-driven block schema generator.

两条路径：
  1. 真实 API — 调 OpenAI Compatible endpoint，system prompt 约束输出为 blocks JSON
  2. Mock — 不调外部 API，按 prompt 关键词走一套预设的"伪 LLM"模板
     （用于无 API key 但想演示 AI 模式效果的场景）

重要：LLM 只负责生成 blocks schema JSON，渲染/事件/持久化全走现有管线。
"""

from __future__ import annotations

import json
import os
import re
import secrets
from typing import Any

# ─── System prompt 约束 ──────────────────────────────────

SYSTEM_PROMPT = """你是一个 Web App Builder。根据用户的自然语言需求，生成一份 blocks schema JSON。

## 输出格式（严格 JSON，不要 markdown）：

{
  "meta": { "brand": "项目名", "accent": "violet|blue|emerald|orange" },
  "blocks": [ ... ]
}

## 可用 block 类型清单：

### 布局类
- layout: { variant: "centered"|"kanban"|"hero", navItems?: [], headerBadge?: "", brand?: "" }
  variant=centered → 居中单列（todo list 风格）
  variant=hero → 全宽顶部 + 下方内容（landing/blog/event 风格）
  variant=kanban → 侧边栏 + 主区（项目管理风格）
- section-nav: { sections: ["概览","我的任务"], active: 0 }

### 内容类
- heading: { text: "...", size: "h1"|"h2"|"h3", eyebrow?: "..." }
- text: { content: "..." }
- button: { label: "...", variant: "primary"|"ghost"|"link", onClick?: "openContactForm" }
- feature-grid: { items: [{icon, title, desc}], columns: 4 }
- pricing-grid: { plans: [{name, price, detail, featured?: bool}], show: true }
- session-list: { sessions: ["上午·xxx", "下午·xxx"] }
- event-hero: { date, headline, eyebrow }

### 交互类
- task-list: {
    placeholder: "...", compact?: bool, showDue?: bool, showProgress?: bool,
    statuses: [{key:"todo",label:"待处理",color:"text-zinc-400 bg-zinc-400/10"}]
  }
  events.handlers 自动声明 { task_create: {action:"upsert", record_type:"task", payload_fields:["title"], defaults:{"status":"todo"}}, task_update, task_delete }
- contact-form: { title: "...", successText: "..." }
  events.handlers 自动声明 { contact: {action:"upsert", record_type:"contact", payload_fields:["name","email"]} }
- registration-form: { capacity: 80, title: "...", successText: "...", sessions: [...] }
  events.handlers 自动声明 { registration: {action:"upsert", record_type:"registration", payload_fields:["name","session"]} }

### 逃生舱（需要任意 HTML/CSS/JS 时用）
- custom-html: { html: "一段 HTML 字符串", js?: "...", css?: "..." }
  直接注入，适合复杂交互或非标准组件

## 约束
- 只能用以上 block 类型，不要发明新类型
- 每个 layout 的 navItems 第一个元素会被当作 header brand 展示
- task-list / contact-form / registration-form 会自动绑定事件 handlers，不需要你写 events 字段
- accent 只能是 violet/blue/emerald/orange 之一
- brand 不超过 24 个字符
"""


# ─── Mock preset library ──────────────────────────────────

def _mock_blog_config(prompt: str) -> dict:
    brand = re.sub(r"[。！!，,]*$", "", prompt[:20]) or "我的博客"
    brand = re.sub(r"^(帮我|做一个|创建)", "", brand) or "我的博客"
    return {
        "meta": {"brand": brand, "accent": "emerald"},
        "blocks": [
            {"id": secrets.token_urlsafe(6), "type": "layout",
             "props": {"variant": "hero", "brand": brand, "navItems": [brand, "首页", "归档", "关于"], "headerBadge": "订阅 RSS"},
             "children": [
                 {"id": secrets.token_urlsafe(6), "type": "heading", "props": {"eyebrow": "WRITING", "text": "持续记录，持续分享。", "size": "h1"}},
                 {"id": secrets.token_urlsafe(6), "type": "text", "props": {"content": "关于产品、工程和思考的一些碎片。"}}
             ]},
            {"id": secrets.token_urlsafe(6), "type": "feature-grid",
             "props": {"columns": 3, "items": [
                 {"icon": "📝", "title": "前端架构", "desc": "React / TypeScript / 设计系统"},
                 {"icon": "⚡", "title": "性能优化", "desc": "构建时 & 运行时的那些事"},
                 {"icon": "🧠", "title": "产品思考", "desc": "用户、价值、取舍"},
                 {"icon": "🛠️", "title": "工具链", "desc": "开发者效率工具分享"},
                 {"icon": "🎨", "title": "设计", "desc": "审美与工程的交叉点"},
                 {"icon": "🚀", "title": "创业", "desc": "从 0 到 1 的真实经历"},
             ]}},
            {"id": secrets.token_urlsafe(6), "type": "task-list",
             "props": {"placeholder": "添加一篇新文章…", "compact": False, "showDue": True, "showProgress": True,
                       "statuses": [
                           {"key": "todo", "label": "草稿", "color": "text-zinc-400 bg-zinc-400/10"},
                           {"key": "in_progress", "label": "写作中", "color": "text-emerald-300 bg-emerald-400/10"},
                           {"key": "done", "label": "已发布", "color": "text-blue-300 bg-blue-400/10"},
                       ]},
             "events": {"source": {"record_type": "post"}, "handlers": {
                 "task_create": {"action": "upsert", "record_type": "post", "payload_fields": ["title"], "defaults": {"status": "todo"}},
                 "task_update": {"action": "update", "record_type": "post", "payload_fields": ["record_id", "status"]},
                 "task_delete": {"action": "delete", "record_type": "post", "payload_fields": ["record_id"]},
             }}},
        ],
    }


def _mock_ecommerce_config(prompt: str) -> dict:
    brand = re.sub(r"[。！!，,]*$", "", prompt[:20]) or "精选商店"
    return {
        "meta": {"brand": brand, "accent": "orange"},
        "blocks": [
            {"id": secrets.token_urlsafe(6), "type": "layout",
             "props": {"variant": "hero", "brand": brand, "navItems": [brand, "全部商品", "新品", "关于"], "headerBadge": "🛒 购物车"},
             "children": [
                 {"id": secrets.token_urlsafe(6), "type": "heading", "props": {"eyebrow": "SHOP THE DROP", "text": "新一季，已到货。", "size": "h1"}},
                 {"id": secrets.token_urlsafe(6), "type": "text", "props": {"content": "精选设计，限量发售。"}},
             ]},
            {"id": secrets.token_urlsafe(6), "type": "custom-html", "props": {
                "html": '''
    <div style="padding: 20px 36px; display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px;">
      <div class="product-card" data-id="p1"><div style="background: rgba(253,186,116,.15); border-radius: 12px; aspect-ratio: 4/3;"></div><h4 style="margin-top:10px; font-size:12px">极简羊毛衫</h4><p style="font-size:11px; color:#fcd34d; margin-top:4px">¥389</p></div>
      <div class="product-card" data-id="p2"><div style="background: rgba(96,165,250,.15); border-radius: 12px; aspect-ratio: 4/3;"></div><h4 style="margin-top:10px; font-size:12px">宽腿休闲裤</h4><p style="font-size:11px; color:#fcd34d; margin-top:4px">¥259</p></div>
      <div class="product-card" data-id="p3"><div style="background: rgba(52,211,153,.15); border-radius: 12px; aspect-ratio: 4/3;"></div><h4 style="margin-top:10px; font-size:12px">手工皮具包</h4><p style="font-size:11px; color:#fcd34d; margin-top:4px">¥599</p></div>
      <div class="product-card" data-id="p4"><div style="background: rgba(167,139,250,.15); border-radius: 12px; aspect-ratio: 4/3;"></div><h4 style="margin-top:10px; font-size:12px">陶瓷马克杯</h4><p style="font-size:11px; color:#fcd34d; margin-top:4px">¥89</p></div>
    </div>
                ''',
                "css": """
    .product-card { border: 1px solid rgba(255,255,255,.08); border-radius: 14px; background: rgba(255,255,255,.02); padding: 12px; cursor: pointer; transition: transform .15s; }
    .product-card:hover { transform: translateY(-2px); border-color: rgba(253,186,116,.3); }
                """,
            }},
            {"id": secrets.token_urlsafe(6), "type": "pricing-grid",
             "props": {"show": False, "plans": []}},
        ],
    }


def _mock_default_config(prompt: str) -> dict:
    """通用兜底：把 prompt 里的关键词塞进 heading，加 task-list"""
    brand = re.sub(r"[。！!，,]*$", "", prompt[:24]) or "新应用"
    brand = re.sub(r"^(帮我|请|做个|创建|做)", "", brand) or brand
    return {
        "meta": {"brand": brand, "accent": "violet"},
        "blocks": [
            {"id": secrets.token_urlsafe(6), "type": "layout",
             "props": {"variant": "centered", "brand": brand},
             "children": [
                 {"id": secrets.token_urlsafe(6), "type": "heading",
                  "props": {"eyebrow": "AI GENERATED", "text": f"为你生成的 {brand}", "size": "h1"}},
                 {"id": secrets.token_urlsafe(6), "type": "text",
                  "props": {"content": "基于你的需求，我整理了一个可编辑的起点。你可以在下方添加或修改内容。"}},
                 {"id": secrets.token_urlsafe(6), "type": "task-list",
                  "props": {"placeholder": "添加一条新内容…", "compact": True, "showDue": False, "showProgress": True,
                            "statuses": [
                                {"key": "todo", "label": "待办", "color": "text-zinc-400 bg-zinc-400/10"},
                                {"key": "done", "label": "已完成", "color": "text-emerald-300 bg-emerald-400/10"},
                            ]},
                  "events": {"source": {"record_type": "task"}, "handlers": {
                      "task_create": {"action": "upsert", "record_type": "task", "payload_fields": ["title"], "defaults": {"status": "todo"}},
                      "task_update": {"action": "update", "record_type": "task", "payload_fields": ["record_id", "status"]},
                      "task_delete": {"action": "delete", "record_type": "task", "payload_fields": ["record_id"]},
                  }}},
             ]},
        ],
    }


_MOCK_PRESETS = [
    (["blog", "博客", "写作", "文章", "post"], _mock_blog_config),
    (["shop", "ecommerce", "电商", "商店", "商品", "购物"], _mock_ecommerce_config),
]


def _mock_generate(prompt: str) -> tuple[dict, list[str]]:
    """根据 prompt 关键词选 mock preset，同时返回 AI 思考过程"""
    lower = prompt.lower()
    for keywords, builder in _MOCK_PRESETS:
        if any(k in lower for k in keywords):
            config = builder(prompt)
            break
    else:
        config = _mock_default_config(prompt)

    brand = config["meta"]["brand"]
    timeline = [
        f"📝 理解需求：「{prompt}」。",
        f"🧭 选择结构：为 {brand} 生成 blocks schema。",
        f"🏗️  组装 {len(config['blocks'])} 个 block：" + " → ".join(b["type"] for b in config["blocks"]),
        "✅ blocks JSON 已生成，写入 app_config。",
        "🧪 自检：每个有交互的 block 都声明了 events handler，持久化走通用 upsert。",
    ]
    return config, timeline


# ─── Real API path ──────────────────────────────────────

def _real_generate(prompt: str, api_key: str, api_base: str, model: str) -> tuple[dict, list[str]]:
    import urllib.request

    payload = {
        "model": model,
        "temperature": 0.4,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    }

    url = api_base.rstrip("/") + "/chat/completions"
    req = urllib.request.Request(
        url,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        data=json.dumps(payload).encode(),
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        raise RuntimeError(f"LLM API 调用失败：{e}") from e

    content = data["choices"][0]["message"]["content"]
    # 清理可能的 ```json 包裹
    content = re.sub(r"^```(json)?\s*", "", content.strip())
    content = re.sub(r"\s*```$", "", content)

    config = json.loads(content)

    # 兜底：确保 meta/blocks 存在
    config.setdefault("meta", {"brand": "新应用", "accent": "violet"})
    config.setdefault("blocks", [])

    timeline = [
        f"📝 理解需求：「{prompt}」。",
        f"🧭 LLM 选择结构：meta={config['meta']}",
        f"🏗️  LLM 生成 {len(config['blocks'])} 个 block：" + " → ".join(b.get("type", "?") for b in config["blocks"]),
        "✅ JSON 解析通过，写入 app_config。",
    ]
    return config, timeline


# ─── Public API ──────────────────────────────────────────

def is_llm_enabled() -> bool:
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    return bool(key)


def get_llm_status() -> dict:
    return {
        "llm_enabled": is_llm_enabled(),
        "provider": os.environ.get("LLM_PROVIDER", "openai"),
        "model": os.environ.get("LLM_MODEL", "gpt-4o-mini"),
        "api_base": os.environ.get("LLM_API_BASE", "https://api.openai.com/v1"),
    }


def generate_app(prompt: str) -> tuple[dict, list[str], bool]:
    """生成 blocks schema + AI 思考 timeline。

    Returns:
        (config_blocks, timeline_messages, used_real_llm)
    """
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    api_base = os.environ.get("LLM_API_BASE", "https://api.openai.com/v1")
    model = os.environ.get("LLM_MODEL", "gpt-4o-mini")

    if api_key:
        try:
            config, timeline = _real_generate(prompt, api_key, api_base, model)
            return config, timeline, True
        except Exception:
            # 真 API 失败，优雅回退到 mock
            config, timeline = _mock_generate(prompt)
            return config, timeline, False

    config, timeline = _mock_generate(prompt)
    return config, timeline, False
