# Atoms Demo

一个可本地部署的 Atoms 风格 AI 应用生成工作台。用户无需登录，即可描述产品想法、查看沉浸式多 Agent 生成过程、对话修改、保存版本，以及发布为可交互的分享页。

## 能力范围

- 三类预设应用：SaaS 落地页、项目管理工作台、活动报名页
- 多 Agent 生成进度（产品 Emma、体验 Iris、架构 Bob、工程 Alex、测试 Luna），每个 Agent 有彩色头像与角色标签
- AI 团队展示：落地页展示 5 个 Agent 的头像、角色与职责描述
- 对话式修改：支持颜色、留白、价格模块、品牌语气等配置迭代
- SQLite 持久化：匿名身份、项目、对话、3 个最近版本，以及任务/报名/表单数据
- 发布分享：`/share/:token` 公开访问；访客可操作生成应用，不能进入工作台
- 生成应用包含功能区、定价区（含推荐标签）、页脚等完整页面结构

## 启动

需要 Docker Desktop。

```bash
docker compose up --build
```

打开 [http://localhost:5173](http://localhost:5173)。后端健康检查为 [http://localhost:8000/api/health](http://localhost:8000/api/health)。

SQLite 文件会持久化到 `backend/data/atoms_demo.db`，停止或重建容器后项目数据仍会保留。

## 本地开发

### 一键启动（推荐）

无需 Docker，一条命令同时启动前后端：

```bash
./dev.sh
```

脚本会自动创建虚拟环境、安装依赖、执行数据库迁移，然后启动前后端服务。按 `Ctrl+C` 停止所有服务。

### 分别启动

前后端可分别启动：

```bash
# 终端 1
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# 终端 2
cd frontend
npm install
npm run dev
```

## 数据库迁移

初始化迁移已包含在 `backend/alembic/versions/0001_initial_schema.py`。在 `backend` 目录中执行：

```bash
alembic upgrade head
```
