#!/bin/bash

# 图文渲染引擎 - 快速测试脚本

echo "========================================"
echo "  图文渲染引擎 - API测试"
echo "========================================"
echo ""

API_BASE="http://localhost:8000/api/render"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试1: 健康检查
echo -e "${YELLOW}测试1: 健康检查${NC}"
curl -s http://localhost:8000/health | python3 -m json.tool
echo ""

# 测试2: 获取平台列表
echo -e "${YELLOW}测试2: 获取支持的平台${NC}"
RESPONSE=$(curl -s "$API_BASE/platforms")
echo "$RESPONSE" | python3 -m json.tool
echo ""

# 测试3: 获取模板列表
echo -e "${YELLOW}测试3: 获取支持的模板${NC}"
curl -s "$API_BASE/templates?platform=xiaohongshu" | python3 -m json.tool
echo ""

# 测试4: 单篇渲染
echo -e "${YELLOW}测试4: 单篇渲染测试${NC}"
echo "正在渲染，请稍候..."
RENDER_RESPONSE=$(curl -s -X POST "$API_BASE/from-text" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "测试标题",
    "content": "禅修的核心智慧在于觉知当下。当我们放下过去的执念，专注于当下的呼吸和感受，内心便能得到真正的宁静。",
    "platform": "xiaohongshu",
    "template": "minimal",
    "author": "@测试账号"
  }')

echo "$RENDER_RESPONSE" | python3 -m json.tool

# 检查是否成功
if echo "$RENDER_RESPONSE" | grep -q '"status": "success"'; then
    echo -e "${GREEN}✓ 渲染成功！${NC}"

    # 提取图片路径
    IMAGE_URL=$(echo "$RENDER_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['images'][0]['url'])" 2>/dev/null)

    if [ -n "$IMAGE_URL" ]; then
        echo -e "${GREEN}图片URL: $IMAGE_URL${NC}"
        FULL_URL="http://localhost:8000$IMAGE_URL"
        echo -e "完整URL: ${GREEN}$FULL_URL${NC}"
    fi
else
    echo -e "${RED}✗ 渲染失败${NC}"
fi
echo ""

# 测试5: 检查生成的文件
echo -e "${YELLOW}测试5: 检查生成的文件${NC}"
if [ -d "data/images" ]; then
    LATEST_DIR=$(ls -td data/images/*/ 2>/dev/null | head -1)
    if [ -n "$LATEST_DIR" ]; then
        echo "最新目录: $LATEST_DIR"
        ls -lh "$LATEST_DIR" 2>/dev/null || echo "目录为空或无权限"
    else
        echo -e "${RED}未找到图片目录${NC}"
    fi
else
    echo -e "${RED}data/images 目录不存在${NC}"
fi
echo ""

echo "========================================"
echo "测试完成"
echo "========================================"
