#!/bin/bash

# 中文字体下载和安装脚本
# 用途：自动下载并安装免费商用的中文字体

echo "========================================="
echo "  中文字体自动安装脚本"
echo "========================================="
echo ""

# 创建临时下载目录
TEMP_DIR=$(mktemp -d)
echo "下载目录: $TEMP_DIR"
cd "$TEMP_DIR"

# 字体下载链接（使用GitHub镜像或官方源）
declare -A FONTS=(
    ["思源黑体"]="https://github.com/adobe-fonts/source-han-sans/releases/download/2.004R/SourceHanSansSC.zip"
    ["思源宋体"]="https://github.com/adobe-fonts/source-han-serif/releases/download/2.001R/SourceHanSerifSC.zip"
)

echo "准备下载以下字体："
for font in "${!FONTS[@]}"; do
    echo "  - $font"
done
echo ""

# 检测操作系统
OS="$(uname -s)"
case "$OS" in
    Linux*)     FONT_DIR="$HOME/.local/share/fonts";;
    Darwin*)    FONT_DIR="$HOME/Library/Fonts";;
    *)          echo "不支持的操作系统: $OS"; exit 1;;
esac

echo "字体安装目录: $FONT_DIR"
echo "创建字体目录..."
mkdir -p "$FONT_DIR"
echo ""

# 下载字体
for font_name in "${!FONTS[@]}"; do
    url="${FONTS[$font_name]}"
    echo "正在下载: $font_name"
    echo "URL: $url"

    if command -v wget >/dev/null 2>&1; then
        wget -q --show-progress "$url" -O "${font_name}.zip"
    elif command -v curl >/dev/null 2>&1; then
        curl -L "$url" -o "${font_name}.zip" --progress-bar
    else
        echo "错误: 需要 wget 或 curl 命令"
        exit 1
    fi

    # 解压
    echo "解压: ${font_name}.zip"
    unzip -q "${font_name}.zip" -d "$font_name"

    # 移动字体文件
    echo "安装字体文件..."
    find "$font_name" -type f \( -name "*.otf" -o -name "*.ttf" -o -name "*.ttc" \) -exec cp {} "$FONT_DIR/" \;

    echo "✓ $font_name 安装完成"
    echo ""
done

# 清理临时文件
echo "清理临时文件..."
cd /
rm -rf "$TEMP_DIR"

# 刷新字体缓存
if [ "$OS" = "Linux" ]; then
    echo "刷新字体缓存..."
    fc-cache -fv >/dev/null 2>&1
fi

echo ""
echo "========================================="
echo "  字体安装完成！"
echo "========================================="
echo ""
echo "已安装的字体："
for font_name in "${!FONTS[@]}"; do
    echo "  ✓ $font_name"
done
echo ""
echo "安装位置: $FONT_DIR"
echo ""
echo "注意："
echo "1. 某些应用可能需要重启才能识别新字体"
echo "2. macOS 用户可能需要在'字体册'应用中验证安装"
echo "3. 如遇问题，请查看: app/skills/skills/generation/render/assets/fonts/README.md"
echo ""
