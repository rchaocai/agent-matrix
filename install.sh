#!/bin/bash

echo "正在安装Agent Matrix依赖..."

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

echo "激活虚拟环境..."
source venv/bin/activate

echo "安装依赖包..."
pip install -r requirements.txt

echo "初始化数据库..."
python scripts/init_db.py

echo "安装完成！"
echo ""
echo "使用以下命令启动应用:"
echo "  source venv/bin/activate"
echo "  uvicorn app.main:app --reload"
