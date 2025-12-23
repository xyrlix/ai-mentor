#!/usr/bin/env bash

# AI Mentor 开发环境启动脚本

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
LOG_DIR="$PROJECT_ROOT/logs"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 停止服务的函数
stop_services() {
    echo "正在停止服务..."
    # 查找并停止后端进程
    BACKEND_PID=$(pgrep -f "uvicorn main:app")
    if [ -n "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo "后端服务已停止 (PID: $BACKEND_PID)"
    fi
    
    # 查找并停止 Celery worker 进程
    CELERY_PIDS=$(pgrep -f "celery -A worker")
    if [ -n "$CELERY_PIDS" ]; then
        kill $CELERY_PIDS 2>/dev/null
        echo "Celery worker 已停止 (PIDs: $CELERY_PIDS)"
    fi
    
    # 查找并停止前端进程
    FRONTEND_PID=$(pgrep -f "vite")
    if [ -n "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        echo "前端服务已停止 (PID: $FRONTEND_PID)"
    fi
    
    exit 0
}

# 捕获中断信号，执行停止服务
trap "stop_services" INT TERM

# 检查并创建后端虚拟环境
if [ ! -d "backend/.venv" ]; then
    echo "创建后端虚拟环境..."
    cd "$BACKEND_DIR"
    python3 -m venv .venv
    . .venv/bin/activate
    pip install -r requirements.txt
    cd "$PROJECT_ROOT"
fi

# 启动后端服务
echo "启动后端服务..."
cd "$BACKEND_DIR"

# 激活虚拟环境并启动后端
if [ -d ".venv" ]; then
    . .venv/bin/activate
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload > "$LOG_DIR/backend.log" 2>&1 &
    BACKEND_PID=$!
    echo "后端服务已启动 (PID: $BACKEND_PID)"
    echo "后端日志: $LOG_DIR/backend.log"
    
    # 启动 Celery worker
    echo "启动 Celery worker..."
    celery -A worker worker --loglevel=info > "$LOG_DIR/celery.log" 2>&1 &
    CELERY_PID=$!
    echo "Celery worker 已启动 (PID: $CELERY_PID)"
    echo "Celery 日志: $LOG_DIR/celery.log"
else
    echo "错误: 后端虚拟环境 .venv 不存在"
    exit 1
fi

# 等待后端启动并检查连接
echo "等待后端服务启动..."

# 增加等待时间，最多等待30秒
for i in {1..30}; do
    if curl -s http://127.0.0.1:8000/health > /dev/null; then
        echo "✅ 后端服务启动成功 (http://127.0.0.1:8000)"
        break
    elif curl -s http://localhost:8000/health > /dev/null; then
        echo "✅ 后端服务启动成功 (http://localhost:8000)"
        break
    else
        if [ $i -eq 30 ]; then
            echo "❌ 后端服务启动失败 - 等待超时"
            echo "检查后端日志: $LOG_DIR/backend.log"
            # 不要杀死进程，让用户查看日志
            echo "进程仍在运行，请检查日志文件了解具体错误"
            break
        else
            echo "等待后端启动... ($i/30)"
            sleep 1
        fi
    fi
done

# 启动前端服务
echo "启动前端服务..."
cd "$FRONTEND_DIR"

# 启动前端
npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "前端服务已启动 (PID: $FRONTEND_PID)"
echo "前端日志: $LOG_DIR/frontend.log"

# 显示启动完成信息
echo ""
echo "========================="
echo "✅ 开发环境启动完成！"
echo "📱 前端地址: http://localhost:5173"
echo "🔧 后端API: http://localhost:8000"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo "========================="
echo ""

# 等待用户中断
wait
