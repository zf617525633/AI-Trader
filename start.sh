#!/bin/bash

# --- 配置 ---
# 获取项目根目录绝对路径
ROOT_DIR=$(pwd)

# --- 1. 启动后端 (API + Worker) ---
echo "🚀 正在启动后端服务..."
cd "$ROOT_DIR/service/server"

# 激活虚拟环境 (优先使用 venv，如果不存在则直接运行)
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 确保日志目录存在
mkdir -p logs

# 启动 API 服务器 (后台运行)
python main.py > logs/api.log 2>&1 &
API_PID=$!

# 启动 Worker 任务 (后台运行，处理价格更新等)
python worker.py > logs/worker.log 2>&1 &
WORKER_PID=$!

echo "✅ 后端 API (PID: $API_PID) 和 Worker (PID: $WORKER_PID) 已在后台启动"

# --- 2. 启动前端 ---
echo "🚀 正在启动前端服务..."
cd "$ROOT_DIR/service/frontend"

# 退出处理函数
cleanup() {
    echo ""
    echo "🛑 正在关闭后端服务 (PID: $API_PID $WORKER_PID)..."
    kill $API_PID $WORKER_PID 2>/dev/null
    echo "👋 服务已关闭"
    exit
}

# 捕获 Ctrl+C (SIGINT) 和 SIGTERM
trap cleanup INT TERM

# 启动前端开发服务器
npm run dev
