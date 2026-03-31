#!/bin/bash

echo "=========================================="
echo "Agent Matrix - 快速启动"
echo "=========================================="
echo ""

# 检查conda环境
if ! conda env list | grep -q "agent-matrix"; then
    echo "错误: agent-matrix conda环境不存在"
    echo "请先运行: conda create -n agent-matrix python=3.10"
    exit 1
fi

# 激活环境
echo "激活 agent-matrix 环境..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate agent-matrix

# 检查数据库
if [ ! -f "data/database.db" ]; then
    echo "初始化数据库..."
    python scripts/init_db.py
fi

# 启动应用
echo ""
echo "启动 Agent Matrix 应用..."
echo "API文档: http://localhost:8000/docs"
echo "健康检查: http://localhost:8000/health"
echo ""
echo "按 Ctrl+C 停止服务器"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
