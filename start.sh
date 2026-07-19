#!/usr/bin/env bash
# Socrates-Cube 一键启动脚本
# 用法: ./start.sh [--mock-mode]

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MOCK_MODE=0
if [[ "${1:-}" == "--mock-mode" ]]; then
  MOCK_MODE=1
fi

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║   Socrates-Cube 多智能体自适应学习系统  一键启动     ║"
echo "║   用法: ./start.sh [--mock-mode]                     ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

cd "$ROOT"

if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1; then
  echo "[错误] 未找到 Python，请先安装 Python 3.10+"
  exit 1
fi

PYTHON_BIN="python3"
command -v python3 >/dev/null 2>&1 || PYTHON_BIN="python"

if [[ ! -d .venv ]]; then
  echo "[1/5] 创建虚拟环境..."
  "$PYTHON_BIN" -m venv .venv
else
  echo "[1/5] 虚拟环境已存在"
fi

echo "[2/5] 激活虚拟环境并安装依赖..."
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -r requirements.txt -q

if [[ ! -f .env ]]; then
  echo "[3/5] 复制环境配置文件..."
  cp .env.example .env
else
  echo "[3/5] 环境配置已存在"
fi

echo "[4/5] 启动后端服务..."
if [[ $MOCK_MODE -eq 1 ]]; then
  echo "      → 后端 Mock 模式启动中 (端口 8000)"
  MOCK_MODE=1 uvicorn src.loopse.main:app --host 0.0.0.0 --port 8000 &
else
  echo "      → 后端正常模式启动中 (端口 8000)"
  uvicorn src.loopse.main:app --reload --host 0.0.0.0 --port 8000 &
fi
BACKEND_PID=$!

sleep 2

echo "[5/5] 启动前端服务..."
cd frontend
if [[ ! -d node_modules ]]; then
  echo "      安装前端依赖..."
  npm install --silent
fi

if [[ $MOCK_MODE -eq 1 ]]; then
  echo "      → 前端 Mock 模式启动中 (端口 5173)"
  npm run dev:mock &
else
  echo "      → 前端正常模式启动中 (端口 5173)"
  npm run dev &
fi
FRONTEND_PID=$!
cd "$ROOT"

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║                ✅ 启动完成！                         ║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║  前端地址:  http://localhost:5173                    ║"
echo "║  后端地址:  http://localhost:8000                    ║"
echo "║  API 文档:  http://localhost:8000/docs               ║"
if [[ $MOCK_MODE -eq 1 ]]; then
echo "║  运行模式:  Mock 模式（离线演示）                   ║"
else
echo "║  运行模式:  正常模式                                 ║"
fi
echo "╠══════════════════════════════════════════════════════╣"
echo "║  按 Ctrl+C 停止所有服务                             ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

cleanup() {
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  echo "👋 服务已停止"
}
trap cleanup EXIT INT TERM
wait
