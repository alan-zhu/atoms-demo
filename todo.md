# Atoms Demo — 笔试说明文档

## 一、实现思路与关键取舍

### 技术栈
| 层 | 选型 | 理由 |
|---|---|---|
| 前端 | React 18 + TypeScript + Vite + Tailwind + react-router-dom | 快速启动、类型安全、样式原子化 |
| 后端 | FastAPI + SQLAlchemy + SQLite | Python 生态对接 LLM 成本最低；SQLite 零配置、demo 够用 |
| 认证 | passlib(bcrypt) + PyJWT | 自实现最小账号体系，避免引入 Auth0/Clerk 等外部依赖 |
| Agent 时间线 | 客户端本地播放（硬编码 5-agent 消息模板） | 省掉服务端流式推送复杂度；消息可引用用户 prompt 关键词模拟真实思考 |
| 应用生成 | 通用 Block Schema（而非模板 if/else 嵌套） | 一次架构改完能支持任意组合；扩展新 block 只需要加函数和事件声明 |
| 持久化 | schema-less `app_records` 表（JSON payload + record_type） | 事件总线读 block 声明做 DB upsert/update/delete，一套逻辑覆盖所有模板 |
| HTML 生成 | 后端实时从 blocks schema 拼自包含 HTML（内联 CSS/JS） | 分享页 iframe 能直接加载；真正独立可运行页面，不是 React mock |
| LLM 生成 | 开关式接入：`OPENAI_API_KEY` 为空走模板，填了走真 LLM | 无 key 时 demo 可运行；有 key 时输出还是 blocks schema，渲染管线不变 |

### 关键取舍
1. **为什么不做前端运行时编译器？** — Vercel v0 那套需要沙箱/eval/import-map，demo 成本太高。用后端 HTML 生成 + iframe 足够展示"可运行"。
2. **为什么 Block Schema 不做通用 JSON 编辑器？** — 目前 11 种 block 硬编码 preset 够用；下一步才需要 LLM 输出任意组合。
3. **为什么账号体系要强制登录？** — 笔试要求"完整基本使用流程"，匿名访客模式体验不完整。注册 → 登录 → 创建 → 分享是完整闭环。
4. **为什么 DB 用 SQLite？** — demo 场景，`docker-compose.yml` 里可以一键换 Postgres，但迁移成本远大于收益。

---

## 二、当前完成程度

### ✅ 已完成
| 模块 | 说明 |
|---|---|
| 侧边栏 / 工作台 UI | 参考 atoms.dev/zh/dashboard 的浅色主题（IBM Plex Sans、主蓝 #4267ff、270px 侧栏） |
| 首页 tab（发现 / 我的项目） | 发现：12 条 mock 模板卡片，支持分类筛选；我的项目：卡片网格 |
| 新建项目流程 | 5 Agent 时间线（产品 / 体验 / 架构 / 工程 / 测试）+ 浮动头像 + PromptBox |
| 通用 Block Schema | layout / heading / text / button / section-nav / task-list / contact-form / feature-grid / pricing-grid / event-hero / session-list / registration-form / custom-html |
| 事件持久化 | `app_records` 表存所有业务数据（任务 / 注册 / 表单），重启不丢 |
| 真实 HTML 生成 | `html_builder.py` 从 blocks schema 拼自包含 HTML，分享页 iframe 加载 |
| Code Viewer | 工作台右侧 Preview / Code 双 tab，展示 HTML 源码 + 一键复制 |
| 分享链接 | `http://localhost:5173/share/{token}` 公开访问，无需登录 |
| 账号体系 | 注册 / 登录 / JWT / bcrypt，强制登录才能使用；分享页保持公开 |
| LLM 开关 | `.env` 配 `OPENAI_API_KEY` 开启 AI 生成，否则走模板路径 |
| Alembic 迁移 | `0001_initial` + `0002_add_users`，新环境一键 up |
| `dev.sh` | 一键启动前后端（前端 5173 / 后端 8000） |

### ⚠️ 部分完成 / 有局限
| 模块 | 现状 |
|---|---|
| Agent 聊天 | 每条消息引用 prompt 关键词 + 按模板类型说不同的话，但还是硬编码模板，不是真 LLM 对话 |
| LLM 生成 | 接了真 API 后输出 blocks schema，但没做 streaming / retry / fallback |
| 生成的应用交互 | Todo list 有真实 CRUD + 状态；SaaS 落地页只有预约演示弹窗；活动报名只有表单 |
| 版本管理 | `POST /api/projects/{id}/iterate` 存了版本快照，但前端没有历史版本查看 UI |
| 部署 | 本地 `dev.sh` 可跑，未部署到公网（评估维度要求"可测试在线访问链接"） |

### ❌ 未做
- 实时协作（多人编辑同一项目）
- 自定义域名 / 部署到 Vercel
- Agent 真对话（接入 LLM 做 iterate 时的多轮上下文）
- 支付 / 积分系统
- 更多 block preset（博客 / 电商商品页 / 评论区 / 日历）
- 单元测试 / e2e

---

## 三、继续投入的扩展方向（优先级排序）

### P0 — 让 demo "更像真产品"
1. **部署到公网** — Fly.io / Railway 跑后端 + DB，Vercel 跑前端，分享链接可对外测试
2. **版本历史 UI** — 工作台左侧显示 v1 / v2 / v3，点哪个看哪个，支持回滚
3. **Agent 多轮对话接 LLM** — iterate 时把历史 message 拼进 prompt，真 LLM 响应，存进 messages 表

### P1 — 扩大生成能力
4. **更多 block preset** — blog-post / product-grid / comment-section / calendar-view，让 "做一个博客网站" 真生成博客而不是 SaaS 落地页
5. **LLM 输出任意 blocks 组合** — 把 `block_schema.py` 的 system prompt 写完整，LLM 可以自己决定用哪些 block、什么顺序；`custom-html` 作为逃生舱
6. **前端 Code Editor** — 工作台右侧 Code tab 改为可编辑，改完点"重新构建"刷新 preview（需要把 HTML 编辑 → blocks schema 反向解析，或者直接 accept 原始 HTML）

### P2 — 打磨体验
7. **发布前预览域名 + QR 码** — 分享弹窗显示二维码，手机扫了直接看
8. **匿名身份隔离** — 分享页的 todo list 按 visitor_id 隔离，而不是所有访客共享一份
9. **错误处理统一** — 现在 error toast 比较粗，应该按错误类型给不同文案（JWT 过期请重新登录、网络失败请检查连接等）
10. **国际化** — 目前全中文硬编码，加 `i18n` 支持英文

### P3 — 加分项
11. **Usage / Credits** — 顶部或侧栏显示"剩余积分 / 本次生成消耗"，接真 LLM 后按 token 计费
12. **AI 生成账单** — 保存每次 LLM 调用的 token 消耗，笔试要求"可选附上 AI coding 工具账单"
13. **Dark mode** — atoms.dev 本身有明暗切换，做起来不难
