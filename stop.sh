#!/usr/bin/env bash

# AI Mentor 开发环境停止脚本

echo "正在停止 AI Mentor 所有服务..."

# 停止后端服务
BACKEND_PID=$(pgrep -f "uvicorn main:app")
if [ -n "$BACKEND_PID" ]; then
    echo "停止后端服务 (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null
    sleep 1
    # 强制停止如果正常停止失败
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo "强制停止后端服务..."
        kill -9 $BACKEND_PID 2>/dev/null
    fi
    echo "✅ 后端服务已停止"
else
    echo "ℹ️  后端服务未运行"
fi

# 停止 Celery worker
CELERY_PIDS=$(pgrep -f "celery -A worker")
if [ -n "$CELERY_PIDS" ]; then
    echo "停止 Celery worker (PIDs: $CELERY_PIDS)..."
    kill $CELERY_PIDS 2>/dev/null
    sleep 1
    # 强制停止如果正常停止失败
    for pid in $CELERY_PIDS; do
        if ps -p $pid > /dev/null 2>&1; then
            echo "强制停止 Celery worker (PID: $pid)..."
            kill -9 $pid 2>/dev/null
        fi
    done
    echo "✅ Celery worker 已停止"
else
    echo "ℹ️  Celery worker 未运行"
fi

# 停止前端服务
FRONTEND_PID=$(pgrep -f "vite")
if [ -n "$FRONTEND_PID" ]; then
    echo "停止前端服务 (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID 2>/dev/null
    sleep 1
    # 强制停止如果正常停止失败
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo "强制停止前端服务..."
        kill -9 $FRONTEND_PID 2>/dev/null
    fi
    echo "✅ 前端服务已停止"
else
    echo "ℹ️  前端服务未运行"
fi

# 停止 npm 相关进程
NPM_PIDS=$(pgrep -f "npm")
if [ -n "$NPM_PIDS" ]; then
    echo "停止 npm 进程 (PIDs: $NPM_PIDS)..."
    kill $NPM_PIDS 2>/dev/null
    sleep 1
    # 强制停止如果正常停止失败
    for pid in $NPM_PIDS; do
        if ps -p $pid > /dev/null 2>&1; then
            echo "强制停止 npm 进程 (PID: $pid)..."
            kill -9 $pid 2>/dev/null
        fi
    done
    echo "✅ npm 进程已停止"
else
    echo "ℹ️  npm 进程未运行"
fi

echo ""
echo "========================="
echo "✅ 所有服务已停止"
echo "========================="