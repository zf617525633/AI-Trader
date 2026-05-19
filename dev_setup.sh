#!/bin/bash

# AI-Trader 一键部署与启动脚本 (macOS/Linux)
# -----------------------------------------

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='
\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== AI-Trader 部署脚本启动 ===${NC}"

# 1. 环境检查
echo -e "\n${YELLOW}[1/4] 检查系统环境...${NC}"

if ! command -v python3 &> /dev/null; then
    echo "错误: 未安装 Python3"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "错误: 未安装 Node.js"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "错误: 未安装 npm"
    exit 1
fi

echo -e "${GREEN}环境检查通过!${NC}"

# 2. 后端配置
echo -e "\n${YELLOW}[2/4] 配置后端服务...${NC}"
cd service/server

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "创建 Python 虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境并安装依赖
source venv/bin/activate
echo "安装后端依赖 (使用镜像源并增加超时)..."
pip install --upgrade pip
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --default-timeout=100 -r ../requirements.txt

# 配置文件处理
if [ ! -f "../../.env" ]; then
    echo "初始化 .env 配置文件..."
    cp "../../.env.example" "../../.env"
    echo -e "${YELLOW}提示: 已根据 .env.example 创建 .env，如需连接真实 API 请手动修改。${NC}"
fi

cd ../..

# 3. 前端配置
echo -e "\n${YELLOW}[3/4] 配置前端服务...${NC}"
cd service/frontend
echo "安装前端依赖 (这可能需要一点时间)..."
npm install
cd ../..

# 4. 启动服务
echo -e "\n${YELLOW}[4/4] 准备启动服务...${NC}"
echo -e "${GREEN}部署完成！${NC}"
echo -e "即将同时启动后端 (8000端口) 和 前端开发服务器。"
echo -e "按 ${YELLOW}Ctrl+C${NC} 停止所有服务。"

# 使用 trap 确保退出时关闭后台进程
trap 'kill $(jobs -p)' EXIT

# 启动后端
echo -e "\n${BLUE}启动后端服务...${NC}"
source service/server/venv/bin/activate
cd service/server
uvicorn main:app --port 8000 &
BACKEND_PID=$!
cd ../..

# 启动前端
echo -e "\n${BLUE}启动前端服务...${NC}"
cd service/frontend
npm run dev &
FRONTEND_PID=$!
cd ../..

# 等待用户中断
wait
