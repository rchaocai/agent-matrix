#!/bin/bash

echo "开始安装思源字体..."

# 创建字体目录
FONT_DIR="$HOME/Library/Fonts"
mkdir -p "$FONT_DIR"

# 创建临时目录
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

echo "下载思源黑体..."
#curl -L "https://github.com/adobe-fonts/source-han-sans/releases/download/2.004R/SourceHanSansSC.zip" -o "SourceHanSansSC.zip" --progress-bar
echo "解压思源黑体..."
unzip -q "/Users/cairuchao/Downloads/SourceHanSansSC.zip"
echo "安装思源黑体..."
find . -type f -name "*.otf" -exec cp {} "$FONT_DIR/" \;

echo "下载思源宋体..."
#curl -L "https://github.com/adobe-fonts/source-han-serif/releases/download/2.003R/09_SourceHanSerifSC.zip" -o "SourceHanSerifSC.zip" --progress-bar
echo "解压思源宋体..."
unzip -q "/Users/cairuchao/Downloads/09_SourceHanSerifSC.zip"
echo "安装思源宋体..."
find . -type f -name "*.otf" -exec cp {} "$FONT_DIR/" \;

# 清理
cd /
rm -rf "$TEMP_DIR"

echo ""
echo "✓ 字体安装完成！"
echo "安装位置: $FONT_DIR"
echo ""
echo "提示：某些应用可能需要重启才能识别新字体"
