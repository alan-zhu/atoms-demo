"""Generate self-contained HTML from project config.

Two paths:
  1. New block schema (config["blocks"] exists) → recursive block renderer
  2. Legacy (old config keys) → original three-template paths
"""

import html
import json
import re
from typing import Any

ACCENTS = {
    "blue": {"grad": "linear-gradient(135deg,#60a5fa,#67e8f9)", "text": "#1e3a8a", "soft": "rgba(96,165,250,.12)", "ring": "rgba(96,165,250,.4)"},
    "emerald": {"grad": "linear-gradient(135deg,#34d399,#5eead4)", "text": "#022c22", "soft": "rgba(52,211,153,.12)", "ring": "rgba(52,211,153,.4)"},
    "orange": {"grad": "linear-gradient(135deg,#fdba74,#fcd34d)", "text": "#431407", "soft": "rgba(253,186,116,.12)", "ring": "rgba(253,186,116,.4)"},
    "violet": {"grad": "linear-gradient(135deg,#a78bfa,#e879f9)", "text": "#2e1065", "soft": "rgba(167,139,250,.12)", "ring": "rgba(167,139,250,.4)"},
}

# SVG icons
SVG_CHECK = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>'
SVG_X = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>'
SVG_PLUS = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>'
SVG_ARROW = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="7" y1="17" x2="17" y2="7"/><polyline points="7 7 17 7 17 17"/></svg>'
SVG_CIRCLE = '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/></svg>'
SVG_CHECK_CIRCLE = '<svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>'
SVG_BADGE = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>'


def _esc(s: Any) -> str:
    if s is None:
        return ""
    return html.escape(str(s))


def _base_css(accent: dict, variant: str = "dark") -> str:
    if variant == "dark":
        body_bg = "#111219"
        text_color = "#f4f4f5"
        return f"""
    :root {{
      --accent-grad: {accent['grad']};
      --accent-text: {accent['text']};
      --accent-soft: {accent['soft']};
      --accent-ring: {accent['ring']};
    }}
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: 'IBM Plex Sans', system-ui, -apple-system, sans-serif; background: {body_bg}; color: {text_color}; min-height: 100vh; }}
    .font-display {{ font-weight: 700; letter-spacing: -0.055em; }}
    """
    return _base_css(accent, "dark")  # 默认深色，不同 block 自己处理背景


def _common_js(token: str, api_base: str) -> str:
    return f"""
    const TOKEN = "{token}";
    const API = "{api_base}";
    let RECORDS = [];

    async function loadProject() {{
      try {{
        const res = await fetch(API + "/api/share/" + TOKEN);
        if (!res.ok) return null;
        return await res.json();
      }} catch(e) {{ return null; }}
    }}

    async function postEvent(evt) {{
      const res = await fetch(API + "/api/share/" + TOKEN + "/events", {{
        method: "POST",
        headers: {{"Content-Type": "application/json"}},
        body: JSON.stringify(evt)
      }});
      if (!res.ok) {{
        const e = await res.json().catch(() => ({{}}));
        alert(e.detail || "操作失败");
        return null;
      }}
      return await res.json();
    }}

    function h(str) {{
      const t = document.createElement('template');
      t.innerHTML = str.trim();
      return t.content.firstChild;
    }}
    """


# ─── Block renderer ─────────────────────────────────────────

def _block_css(accent: dict) -> str:
    return f"""
    /* Layouts */
    .layout {{ min-height: 100vh; }}
    .layout.kanban {{ display: grid; grid-template-columns: 150px 1fr; }}
    .layout.centered {{ display: flex; flex-direction: column; align-items: center; max-width: 560px; margin: 0 auto; padding: 56px 24px 40px; }}
    .layout.hero {{ position: relative; }}

    /* Header */
    .app-header {{ display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,.07); padding: 16px 20px; }}
    .app-header .brand {{ display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 700; letter-spacing: -0.03em; }}
    .app-header .brand-badge {{ width: 24px; height: 24px; border-radius: 6px; background: var(--accent-grad); display: grid; place-items: center; color: var(--accent-text); }}
    .app-header .nav-items {{ display: flex; gap: 16px; font-size: 11px; color: #a1a1aa; }}
    .app-header .header-btn {{ background: rgba(255,255,255,.05); border: 1px solid rgba(255,255,255,.1); color: #e4e4e7; border-radius: 8px; padding: 6px 12px; font-size: 11px; cursor: pointer; }}
    .app-header .status-pill {{ background: rgba(52,211,153,.1); border-radius: 999px; padding: 4px 8px; font-size: 9px; color: #34d399; display: flex; align-items: center; gap: 4px; }}
    .app-header .status-dot {{ width: 6px; height: 6px; border-radius: 50%; background: #34d399; }}

    /* Section nav */
    .section-nav {{ border-right: 1px solid rgba(255,255,255,.07); padding: 12px; }}
    .section-nav button {{ display: flex; align-items: center; gap: 8px; width: 100%; text-align: left; border: none; background: none; border-radius: 6px; padding: 8px 10px; font-size: 11px; color: #71717a; cursor: pointer; margin-bottom: 4px; }}
    .section-nav button:hover {{ background: rgba(255,255,255,.04); }}
    .section-nav button.active {{ background: rgba(255,255,255,.07); color: #f4f4f5; }}
    .section-nav button.active svg {{ color: var(--accent-text); }}

    /* Heading */
    .heading-eyebrow {{ font-size: 10px; font-weight: 500; letter-spacing: 0.15em; color: var(--accent-text); margin-bottom: 10px; }}
    .heading-h1 {{ font-size: 40px; line-height: 1.1; margin-top: 10px; }}
    .heading-h2 {{ font-size: 24px; margin-top: 10px; }}
    .heading-h3 {{ font-size: 18px; margin-top: 10px; }}

    /* Text */
    .block-text {{ margin-top: 8px; font-size: 13px; color: #71717a; line-height: 1.5; }}

    /* Buttons */
    .btn-row {{ display: flex; gap: 10px; margin-top: 20px; }}
    .btn {{ border-radius: 8px; padding: 10px 16px; font-size: 12px; font-weight: 600; cursor: pointer; border: none; display: inline-flex; align-items: center; gap: 4px; }}
    .btn-primary {{ background: var(--accent-grad); color: var(--accent-text); }}
    .btn-ghost {{ background: transparent; border: 1px solid rgba(255,255,255,.1); color: #d4d4d8; }}

    /* Task list */
    .task-stats {{ display: flex; align-items: center; gap: 14px; margin-top: 28px; font-size: 11px; color: #71717a; }}
    .task-progress {{ flex: 1; height: 4px; background: rgba(255,255,255,.08); border-radius: 2px; overflow: hidden; }}
    .task-progress-bar {{ height: 100%; background: var(--accent-grad); border-radius: 2px; width: 0%; transition: width .3s; }}
    .task-form {{ margin-top: 24px; display: flex; gap: 8px; }}
    .task-input {{ flex: 1; border: 1px solid rgba(255,255,255,.08); background: rgba(0,0,0,.2); border-radius: 8px; padding: 10px 12px; font-size: 12px; color: #f4f4f5; outline: none; }}
    .task-input:focus {{ border-color: var(--accent-ring); }}
    .task-add-btn {{ width: 36px; border: none; border-radius: 8px; background: var(--accent-grad); color: var(--accent-text); cursor: pointer; display: grid; place-items: center; }}
    .task-list {{ margin-top: 16px; display: flex; flex-direction: column; gap: 8px; }}
    .task-row {{ display: flex; align-items: center; gap: 12px; border: 1px solid rgba(255,255,255,.07); background: rgba(255,255,255,.025); border-radius: 12px; padding: 12px; }}
    .task-check {{ width: 20px; height: 20px; border-radius: 50%; border: 1px solid #52525b; display: grid; place-items: center; cursor: pointer; flex-shrink: 0; background: none; color: transparent; }}
    .task-check.done {{ border-color: #34d399; background: #34d399; color: #022c22; }}
    .task-title {{ flex: 1; font-size: 12px; }}
    .task-title.done {{ color: #52525b; text-decoration: line-through; }}
    .task-status {{ border-radius: 999px; padding: 2px 8px; font-size: 9px; cursor: pointer; border: none; }}
    .task-due {{ font-size: 10px; color: #52525b; }}
    .task-delete {{ background: none; border: none; color: #3f3f46; cursor: pointer; opacity: 0; transition: opacity .15s; }}
    .task-row:hover .task-delete {{ opacity: 1; }}
    .task-delete:hover {{ color: #fda4af; }}

    /* Feature grid */
    .feature-grid {{ margin-top: 24px; display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px; padding: 0 36px; }}
    .feature-card {{ border: 1px solid rgba(255,255,255,.08); background: rgba(0,0,0,.15); border-radius: 12px; padding: 16px; }}
    .feature-icon {{ font-size: 18px; }}
    .feature-title {{ margin-top: 8px; font-size: 12px; font-weight: 600; color: #e4e4e7; }}
    .feature-desc {{ margin-top: 4px; font-size: 10px; line-height: 1.5; color: #71717a; }}

    /* Pricing grid */
    .pricing-grid {{ margin-top: 16px; display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 8px; padding: 0 36px; }}
    .plan-card {{ border: 1px solid rgba(255,255,255,.08); background: rgba(0,0,0,.15); border-radius: 12px; padding: 16px; position: relative; }}
    .plan-card.featured {{ border-color: rgba(167,139,250,.3); background: var(--accent-soft); }}
    .plan-name {{ font-size: 11px; color: #a1a1aa; }}
    .plan-price {{ margin-top: 12px; font-size: 24px; font-weight: 700; letter-spacing: -0.05em; }}
    .plan-detail {{ margin-top: 8px; font-size: 10px; color: #71717a; }}
    .plan-badge {{ margin-top: 12px; display: inline-block; background: var(--accent-soft); border-radius: 999px; padding: 2px 8px; font-size: 9px; color: var(--accent-text); }}

    /* Contact form modal */
    .modal-overlay {{ position: fixed; inset: 0; z-index: 10; display: grid; place-items: center; background: rgba(0,0,0,.7); backdrop-filter: blur(4px); }}
    .modal-card {{ width: 100%; max-width: 380px; border: 1px solid rgba(255,255,255,.1); background: #1a1a22; border-radius: 16px; padding: 20px; margin: 20px; }}
    .modal-close {{ float: right; background: none; border: none; color: #71717a; cursor: pointer; }}
    .modal-title {{ font-size: 20px; }}
    .modal-sub {{ margin-top: 4px; font-size: 12px; color: #71717a; }}
    .modal-input {{ margin-top: 20px; width: 100%; border: 1px solid rgba(255,255,255,.09); background: rgba(0,0,0,.2); border-radius: 8px; padding: 10px 12px; font-size: 12px; color: #f4f4f5; outline: none; }}
    .modal-input:focus {{ border-color: var(--accent-ring); }}
    .modal-input:nth-of-type(2) {{ margin-top: 8px; }}
    .modal-submit {{ margin-top: 12px; width: 100%; border-radius: 8px; padding: 10px; font-size: 12px; border: none; background: var(--accent-grad); color: var(--accent-text); font-weight: 700; cursor: pointer; }}
    .success-panel {{ text-align: center; padding: 32px 0; color: #6ee7b7; }}

    /* Landing hero area */
    .landing-hero {{ position: relative; max-width: 560px; padding: 56px 36px; }}
    .landing-pill {{ display: inline-block; border: 1px solid rgba(255,255,255,.1); background: rgba(255,255,255,.04); border-radius: 999px; padding: 4px 10px; font-size: 9px; letter-spacing: 0.15em; color: #d4d4d8; margin-bottom: 16px; }}

    /* Event hero area */
    .event-hero {{ position: relative; border-bottom: 1px solid rgba(254,243,199,.1); padding: 20px 32px; background: #15100e; }}
    .event-date {{ font-size: 11px; color: rgba(254,215,170,.6); margin-bottom: 16px; }}
    .event-eyebrow {{ font-size: 10px; letter-spacing: 0.16em; color: rgba(254,243,199,.5); text-align: right; }}
    .event-content {{ max-width: 420px; padding: 40px 0; }}
    .event-content h1 {{ font-size: 48px; line-height: 1.02; }}
    .event-content p {{ margin-top: 20px; max-width: 420px; font-size: 14px; line-height: 1.5; color: rgba(254,243,199,.6); }}

    /* Event body grid */
    .event-body-grid {{ display: grid; grid-template-columns: 1fr 0.9fr; gap: 20px; padding: 20px 32px; background: #15100e; color: #fff7ed; }}
    .event-blob {{ position: absolute; right: -80px; top: -64px; width: 208px; height: 208px; border-radius: 50%; background: rgba(253,186,116,.2); filter: blur(60px); }}
    .event-section-label {{ font-size: 10px; letter-spacing: 0.14em; color: rgba(254,215,170,.5); }}
    .session-item {{ display: flex; align-items: center; gap: 12px; border: 1px solid rgba(254,243,199,.1); background: rgba(254,243,199,.035); border-radius: 12px; padding: 12px; margin-bottom: 8px; }}
    .session-num {{ width: 24px; height: 24px; border-radius: 50%; background: rgba(254,215,170,.1); display: grid; place-items: center; font-size: 10px; color: #fcd34d; flex-shrink: 0; }}
    .reg-card {{ border: 1px solid rgba(254,243,199,.12); background: rgba(0,0,0,.2); border-radius: 16px; padding: 20px; }}
    .reg-input {{ margin-top: 20px; width: 100%; border: 1px solid rgba(254,243,199,.1); background: rgba(0,0,0,.2); border-radius: 8px; padding: 10px 12px; font-size: 12px; color: #fff7ed; outline: none; }}
    .reg-input:focus {{ border-color: rgba(254,215,170,.4); }}
    .reg-select {{ margin-top: 8px; width: 100%; border: 1px solid rgba(254,243,199,.1); background: #1b1310; border-radius: 8px; padding: 10px 12px; font-size: 12px; color: #fff7ed; outline: none; }}
    .reg-submit {{ margin-top: 12px; width: 100%; border-radius: 8px; padding: 10px; font-size: 12px; border: none; background: rgba(253,186,116,.9); color: #431407; font-weight: 700; cursor: pointer; }}
    .reg-count {{ margin-top: 12px; font-size: 11px; color: rgba(254,243,199,.45); }}
    .reg-count span {{ color: #fcd34d; }}

    .footer {{ margin-top: 40px; border-top: 1px solid rgba(255,255,255,.07); padding: 20px; text-align: center; font-size: 10px; color: #52525b; }}
    """


def _render_block(block: dict, accent: dict, js_parts: list[str]) -> str:
    """递归渲染单个 block，收集 inline JS 到 js_parts"""
    btype = block["type"]
    props = block.get("props", {})

    if btype == "layout":
        return _render_layout(block, accent, js_parts)
    if btype == "heading":
        size = props.get("size", "h1")
        cls = f"heading-{size}"
        eyebrow_html = f'<div class="heading-eyebrow">{_esc(props.get("eyebrow", ""))}</div>' if props.get("eyebrow") else ""
        return f'<div class="{cls} font-display">{eyebrow_html}{_esc(props.get("text", ""))}</div>'
    if btype == "text":
        return f'<div class="block-text">{_esc(props.get("content", ""))}</div>'
    if btype == "button":
        label = _esc(props.get("label", ""))
        variant = props.get("variant", "primary")
        cls = f"btn btn-{variant}"
        onclick = ""
        if props.get("onClick") == "openContactForm":
            onclick = ' onclick="openContactForm()"'
        arrow = SVG_ARROW if variant == "primary" else ""
        return f'<div class="btn-row"><button class="{cls}"{onclick}>{label} {arrow}</button></div>'
    if btype == "section-nav":
        items_html = "".join(
            f'<button class="{"active" if i == props.get("active", 0) else ""}">{SVG_CIRCLE}<span>{_esc(s)}</span></button>'
            for i, s in enumerate(props.get("sections", []))
        )
        return f'<div class="section-nav">{items_html}</div>'
    if btype == "feature-grid":
        items_html = "".join(
            f'<div class="feature-card"><div class="feature-icon">{_esc(item.get("icon", ""))}</div><div class="feature-title">{_esc(item.get("title", ""))}</div><p class="feature-desc">{_esc(item.get("desc", ""))}</p></div>'
            for item in props.get("items", [])
        )
        return f'<div class="feature-grid">{items_html}</div>'
    if btype == "pricing-grid":
        if not props.get("show", True):
            return ""
        plans_html = "".join(
            f'<div class="plan-card {"featured" if plan.get("featured") else ""}"><span class="plan-name">{_esc(plan["name"])}</span><div class="plan-price">{_esc(plan["price"])}</div><p class="plan-detail">{_esc(plan["detail"])}</p>{'<span class="plan-badge">推荐</span>' if plan.get("featured") else ""}</div>'
            for plan in props.get("plans", [])
        )
        return f'<div class="pricing-grid">{plans_html}</div>'
    if btype == "contact-form":
        # 加 modal + openForm JS
        js_parts.append("""
    function openContactForm() { document.getElementById('formModal').style.display = 'grid'; }
    function closeContactForm() { document.getElementById('formModal').style.display = 'none'; }
    async function submitContact(e) {
      e.preventDefault();
      const data = new FormData(e.target);
      const res = await postEvent({type: 'contact', payload: {name: data.get('name'), email: data.get('email')}});
      if (res) { document.getElementById('formContent').style.display = 'none'; document.getElementById('formSuccess').style.display = 'block'; }
    }
        """)
        return f'''
    <div class="btn-row">
      <button class="btn btn-primary" onclick="openContactForm()">预约演示 {SVG_ARROW}</button>
    </div>
    <div class="modal-overlay" id="formModal" style="display:none">
      <div class="modal-card">
        <button class="modal-close" onclick="closeContactForm()">{SVG_X}</button>
        <div id="formContent">
          <h3 class="modal-title font-display">{_esc(props.get("title", "预约产品演示"))}</h3>
          <p class="modal-sub">{_esc(props.get("successText", "留下联系方式"))}</p>
          <form onsubmit="submitContact(e)">
            <input name="name" placeholder="你的名字" required class="modal-input" />
            <input name="email" type="email" placeholder="工作邮箱" required class="modal-input" />
            <button type="submit" class="modal-submit">提交预约</button>
          </form>
        </div>
        <div id="formSuccess" style="display:none" class="success-panel">
          {SVG_CHECK_CIRCLE}
          <h3 class="font-display" style="font-size:20px;margin-top:12px">{_esc(props.get("successText", "收到你的信息"))}</h3>
        </div>
      </div>
    </div>
        '''
    if btype == "task-list":
        return _render_task_list(block, js_parts)
    if btype == "event-hero":
        date = _esc(props.get("date", ""))
        eyebrow = _esc(props.get("eyebrow", ""))
        headline = _esc(props.get("headline", ""))
        return f'''
    <div class="event-hero">
      <div class="event-blob"></div>
      <div style="display:flex;align-items:center;justify-content:space-between">
        <span class="font-display text-base font-semibold tracking-[-.04em]">·</span>
        <span class="event-eyebrow">{eyebrow}</span>
      </div>
      <div class="event-content">
        <p class="event-date">{date}</p>
        <h1 class="font-display">{headline}</h1>
      </div>
    </div>
        '''
    if btype == "session-list":
        items_html = "".join(
            f'<div class="session-item"><span class="session-num">0{i+1}</span><span>{_esc(s)}</span></div>'
            for i, s in enumerate(props.get("sessions", []))
        )
        return f'<div><p class="event-section-label">CHOOSE YOUR PATH</p><div style="margin-top:12px">{items_html}</div></div>'
    if btype == "registration-form":
        js_parts.append("""
    let REG_COUNT = 0;
    function renderRegs() {
      REG_COUNT = RECORDS.filter(r => r.record_type === 'registration').length;
      document.getElementById('regCount').textContent = REG_COUNT;
    }
    async function submitReg(e) {
      e.preventDefault();
      const data = new FormData(e.target);
      const res = await postEvent({type: 'registration', payload: {name: data.get('name'), session: data.get('session')}});
      if (res) {
        RECORDS = res.records || [];
        document.getElementById('regForm').style.display = 'none';
        document.getElementById('regSuccess').style.display = 'block';
      }
    }
        """)
        sessions = props.get("sessions", ["上午", "下午", "晚上"])
        return f'''
    <div class="reg-card">
      <div id="regForm">
        <h3 class="font-display text-xl">预留一个席位</h3>
        <p class="modal-sub" style="margin-top:4px">名额有限，提交后即完成报名。</p>
        <form onsubmit="submitReg(e)">
          <input name="name" placeholder="你的名字" required class="reg-input" />
          <select name="session" required class="reg-select" style="margin-top:8px">
            <option value="" disabled selected>选择参与场次</option>
            {''.join(f'<option>{_esc(s)}</option>' for s in sessions)}
          </select>
          <button type="submit" class="reg-submit">确认报名 {SVG_ARROW}</button>
        </form>
        <p class="reg-count">已报名 <span id="regCount">0</span> / {props.get("capacity", 80)}</p>
      </div>
      <div id="regSuccess" style="display:none" class="success-panel">
        {SVG_CHECK_CIRCLE}
        <h3 class="font-display" style="font-size:20px;margin-top:12px">{_esc(props.get("successText", "你已在名单中"))}</h3>
      </div>
    </div>
        '''
    if btype == "custom-html":
        # 逃生舱：直接注入 HTML，可选附加 JS/CSS
        html_str = props.get("html", "")
        extra_js = props.get("js")
        extra_css = props.get("css")
        if extra_js:
            js_parts.append(f"\n    // custom-html inline script\n    {extra_js}\n")
        if extra_css:
            return f'<style>{extra_css}</style>\n{html_str}'
        return html_str

    return f'<!-- unknown block: {btype} -->'


def _render_layout(block: dict, accent: dict, js_parts: list[str]) -> str:
    props = block.get("props", {})
    variant = props.get("variant", "hero")
    brand = props.get("navItems", [""])[0] if props.get("navItems") else ""  # 从 meta 取 brand

    # header
    nav_items_html = "".join(f"<span>{_esc(n)}</span>" for n in props.get("navItems", []))
    header_btn = ""
    if props.get("headerBadge"):
        header_btn = f'<span class="header-btn">{_esc(props["headerBadge"])}</span>'

    if variant == "hero":
        header_html = f'''
        <div style="display:flex;align-items:center;justify-content:space-between;padding:20px 36px;border-bottom:1px solid rgba(255,255,255,.07)">
          <span class="font-display">{_esc(props.get("navItems", [""])[0]) if props.get("navItems") else ""}</span>
          <div style="display:flex;gap:20px;font-size:11px;color:#a1a1aa">{nav_items_html}</div>
          {header_btn}
        </div>
        '''
    elif variant == "kanban":
        header_html = f'''
        <header class="app-header">
          <div class="brand">
            <div class="brand-badge">{SVG_BADGE}</div>
            <span class="font-display">{_esc(props.get("navItems", [""])[0]) if props.get("navItems") else ""}</span>
          </div>
          <span class="status-pill"><span class="status-dot"></span>{_esc(props.get("headerBadge", "同步正常"))}</span>
        </header>
        '''
    else:  # centered
        header_html = f'''
        <header class="app-header">
          <div class="brand">
            <div class="brand-badge">{SVG_BADGE}</div>
            <span class="font-display">{_esc(props.get("navItems", [""])[0]) if props.get("navItems") else ""}</span>
          </div>
          <span class="status-pill"><span class="status-dot"></span>自动保存</span>
        </header>
        '''

    # body blocks
    children_html = "".join(_render_block(c, accent, js_parts) for c in block.get("children", []))

    cls = f"layout {variant}"
    return f'<div class="{cls}">{header_html}{children_html}</div>'


def _render_task_list(block: dict, js_parts: list[str]) -> str:
    props = block.get("props", {})
    statuses = props.get("statuses", [])
    states_obj = json.dumps({s["key"]: {"label": s["label"], "color": "white"} for s in statuses})
    colors_obj = json.dumps({s["key"]: s["color"] for s in statuses})

    js_parts.append(f"""
    function renderTasks() {{
      const tasks = RECORDS.filter(r => r.record_type === 'task');
      const list = document.getElementById('taskList');
      list.innerHTML = '';
      let done = 0;
      const states = {states_obj};
      const colors = {colors_obj};
      tasks.forEach(t => {{
        const status = t.payload.status || 'todo';
        if (status === 'done') done++;
        const st = colors[status] ? colors[status].split(' ') : ['#a1a1aa', 'rgba(161,161,170,.1)'];
        const cls = status === 'done' ? 'task-check done' : 'task-check';
        const titleCls = status === 'done' ? 'task-title done' : 'task-title';
        const el = document.createElement('div');
        el.className = 'task-row';
        el.innerHTML = '<button class="' + cls + '" data-id="' + t.id + '" data-action="toggle">{SVG_CHECK}</button>'
          + '<span class="' + titleCls + '">' + t.payload.title + '</span>'
          + '<button class="task-status" data-id="' + t.id + '" data-action="cycle" style="color:' + st[0] + ';background:' + st[1] + '">' + (states[status]?.label || status) + '</button>'
          + '<button class="task-delete" data-id="' + t.id + '" data-action="delete">{SVG_X}</button>';
        list.appendChild(el);
      }});
      document.getElementById('doneCount').textContent = done;
      document.getElementById('totalCount').textContent = tasks.length;
      const bar = document.getElementById('progressBar');
      if (bar) bar.style.width = tasks.length > 0 ? (done / tasks.length * 100) + '%' : '0%';
    }}
    async function addTask(e) {{
      e.preventDefault();
      const input = document.getElementById('taskInput');
      if (!input.value.trim()) return;
      const res = await postEvent({{type: 'task_create', payload: {{title: input.value}}}});
      if (res) {{ RECORDS = res.records || []; renderTasks(); input.value = ''; }}
    }}
    document.getElementById('taskList').addEventListener('click', async function(e) {{
      const btn = e.target.closest('[data-action]');
      if (!btn) return;
      const id = btn.dataset.id;
      const action = btn.dataset.action;
      const task = RECORDS.find(r => r.id === id);
      if (!task) return;
      if (action === 'toggle') {{
        const res = await postEvent({{type: 'task_update', payload: {{record_id: id, status: task.payload.status === 'done' ? 'todo' : 'done'}}}});
        if (res) {{ RECORDS = res.records || []; renderTasks(); }}
      }} else if (action === 'cycle') {{
        const res = await postEvent({{type: 'task_update', payload: {{record_id: id, status: task.payload.status === 'todo' ? 'in_progress' : 'todo'}}}});
        if (res) {{ RECORDS = res.records || []; renderTasks(); }}
      }} else if (action === 'delete') {{
        const res = await postEvent({{type: 'task_delete', payload: {{record_id: id}}}});
        if (res) {{ RECORDS = res.records || []; renderTasks(); }}
      }}
    }});
    """)

    show_progress = props.get("showProgress", True)
    progress_html = '<div class="task-progress"><div class="task-progress-bar" id="progressBar"></div></div>' if show_progress else ""
    placeholder = _esc(props.get("placeholder", "添加一个新任务…"))
    return f'''
    <div class="task-stats">
      <span>完成 <span id="doneCount">0</span> / <span id="totalCount">0</span></span>
      {progress_html}
    </div>
    <form class="task-form" onsubmit="addTask(event)">
      <input id="taskInput" placeholder="{placeholder}" class="task-input" />
      <button type="submit" class="task-add-btn">{SVG_PLUS}</button>
    </form>
    <div class="task-list" id="taskList"></div>
    '''


# ─── Legacy template renderers (old config keys) ─────────

def _legacy_landing(config: dict, accent: dict) -> tuple[str, str]:
    brand = _esc(config.get("brand", ""))
    eyebrow = _esc(config.get("eyebrow", ""))
    headline = _esc(config.get("headline", ""))
    description = _esc(config.get("description", ""))
    show_pricing = config.get("show_pricing", True)
    plans = config.get("plans", [])
    features = [("⚡", "极速启动", "从想法到上线，只需几分钟"), ("🎨", "精美设计", "每个像素都经过精心打磨"), ("🔄", "持续迭代", "对话式修改，实时预览效果"), ("📊", "数据驱动", "内置分析，洞察每一个用户行为")]

    feature_html = "".join(
        f'<div class="feature-card"><div class="feature-icon">{ic}</div><div class="feature-title">{_esc(t)}</div><p class="feature-desc">{_esc(d)}</p></div>'
        for ic, t, d in features
    )
    pricing_html = ""
    if show_pricing and plans:
        parts = []
        for i, p in enumerate(plans):
            feat = "featured" if i == 1 else ""
            badge = '<span class="plan-badge">推荐</span>' if i == 1 else ""
            parts.append(
                f'<div class="plan-card {feat}">'
                f'<span class="plan-name">{_esc(p["name"])}</span>'
                f'<div class="plan-price">{_esc(p["price"])}</div>'
                f'<p class="plan-detail">{_esc(p["detail"])}</p>'
                f"{badge}</div>"
            )
        pricing_html = f'<div class="pricing-grid">{"".join(parts)}</div>'

    body = f'''
    <div style="position:absolute;right:-80px;top:-80px;width:320px;height:320px;border-radius:50%;background:var(--accent-grad);opacity:.18;filter:blur(60px)"></div>
    <div style="display:flex;align-items:center;justify-content:space-between;padding:20px 36px;border-bottom:1px solid rgba(255,255,255,.07)">
      <span class="font-display">{brand}</span>
      <div style="display:flex;gap:20px;font-size:11px;color:#a1a1aa"><span>产品</span><span>方案</span><span>客户</span></div>
      <div class="header-btn">预约演示</div>
    </div>
    <div class="landing-hero">
      <div class="landing-pill">{eyebrow}</div>
      <h1 class="font-display" style="font-size:48px;line-height:1.03">{headline}</h1>
      <p style="margin-top:20px;max-width:420px;font-size:14px;color:#a1a1aa">{description}</p>
      <div class="btn-row">
        <button class="btn btn-primary" onclick="openContactForm()">开始体验 {SVG_ARROW}</button>
        <button class="btn btn-ghost">了解更多</button>
      </div>
    </div>
    <div class="feature-grid">{feature_html}</div>
    {pricing_html}
    '''

    js = '''
    function openContactForm() { document.getElementById('formModal').style.display = 'grid'; }
    function closeContactForm() { document.getElementById('formModal').style.display = 'none'; }
    async function submitContact(e) {
      e.preventDefault();
      const data = new FormData(e.target);
      const res = await postEvent({type: 'contact', payload: {name: data.get('name'), email: data.get('email')}});
      if (res) { document.getElementById('formContent').style.display = 'none'; document.getElementById('formSuccess').style.display = 'block'; }
    }
    '''
    return body, js


# ─── Public API ────────────────────────────────────────────

def generate_html(template_type: str, config: dict, *, share_token: str, api_base: str = "") -> str:
    accent_key = str(config.get("accent", "violet"))
    accent = ACCENTS.get(accent_key, ACCENTS["violet"])
    common_js = _common_js(share_token, api_base)

    css = _base_css(accent) + _block_css(accent)
    config_json = json.dumps(config, ensure_ascii=False)

    # New block schema
    if "blocks" in config:
        js_parts: list[str] = []
        body_html = "".join(_render_block(b, accent, js_parts) for b in config["blocks"])
        combined_js = common_js + "\n    const CONFIG = " + config_json + ";\n" + "\n".join(js_parts) + """
    document.addEventListener("DOMContentLoaded", async function() {
      const p = await loadProject();
      if (p) { RECORDS = p.records || []; }
      if (typeof renderTasks === 'function') renderTasks();
      if (typeof renderRegs === 'function') renderRegs();
      if (typeof renderRegsCount === 'function') renderRegsCount();
    });
        """
        body_class = f"atoms-{_esc(template_type)}"
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{_esc(config.get('meta', {}).get('brand', 'Atoms App'))}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet" />
  <style>{css}</style>
</head>
<body class="{body_class}">{body_html}
  <script>{combined_js}</script>
</body>
</html>"""

    # Legacy path — old config keys
    if template_type == "landing":
        body_html, body_js = _legacy_landing(config, accent)
    else:
        body_html, body_js = "", ""

    # Wrap with common legacy JS
    combined_js = common_js + "\n    const CONFIG = " + config_json + ";\n" + body_js + """
    document.addEventListener("DOMContentLoaded", async function() {
      const p = await loadProject();
      if (p) { RECORDS = p.records || []; }
    });
    """
    body_class = f"atoms-{_esc(template_type)}"
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{_esc(config.get('brand', 'Atoms App'))}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet" />
  <style>{css}</style>
</head>
<body class="{body_class}">{body_html}
  <script>{combined_js}</script>
</body>
</html>"""
