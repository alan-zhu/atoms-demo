#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

cleanup() {
  echo "\n正在停止服务..."
  [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null
  [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null
  wait 2>/dev/null
  echo "已停止。"
}
trap cleanup EXIT INT TERM

# --- Backend ---
echo "[1/2] 启动后端 (http://localhost:8000)..."
cd "$BACKEND_DIR"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

# --- Frontend ---
echo "[2/2] 启动前端 (http://localhost:5173)..."
cd "$FRONTEND_DIR"
[ ! -d "node_modules" ] && npm install
npm run dev &
FRONTEND_PID=$!

echo "\n✓ 服务已启动：
  前端:  http://localhost:5173
  后端:  http://localhost:8000/api/health
  按 Ctrl+C 停止所有服务\n"

wait
