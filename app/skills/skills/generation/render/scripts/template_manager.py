"""
模板管理器 - 加载和渲染 HTML 模板
"""

import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.async_api import async_playwright
import urllib.parse


class TemplateManager:
    """模板管理器"""

    def __init__(
        self,
        template_dir: str = "app/skills/skills/generation/render/assets/templates",
    ):
        self.template_dir = Path(template_dir)
        self.jinja_env = self._create_jinja_environment()

    def _create_jinja_environment(self) -> Environment:
        """创建 Jinja2 环境"""
        # 检查模板目录是否存在
        if not self.template_dir.exists():
            print(f"Warning: Template directory {self.template_dir} does not exist")
            # 创建默认模板
            self._create_default_templates()

        return Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def _create_default_templates(self):
        """创建默认模板"""
        self.template_dir.mkdir(parents=True, exist_ok=True)

        # 创建基础布局模板
        base_template = self.template_dir / "base" / "layout.html"
        base_template.parent.mkdir(parents=True, exist_ok=True)

        if not base_template.exists():
            base_template.write_text(
                """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: {{ config.fonts.body.family }};
            background-color: {{ config.colors.background }};
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }

        .container {
            width: {{ config.width }}px;
            height: {{ config.height }}px;
            background-color: {{ config.colors.background }};
            padding: {{ config.spacing.padding_top }}px {{ config.spacing.padding_right }}px {{ config.spacing.padding_bottom }}px {{ config.spacing.padding_left }}px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .title {
            font-family: {{ config.fonts.title.family }};
            font-size: {{ config.fonts.title.size }}px;
            font-weight: {{ config.fonts.title.weight }};
            color: {{ config.fonts.title.color }};
            line-height: {{ config.fonts.title.line_height }};
            margin-bottom: 60px;
            text-align: {{ title_align or 'center' }};
        }

        .content {
            font-family: {{ config.fonts.body.family }};
            font-size: {{ config.fonts.body.size }}px;
            font-weight: {{ config.fonts.body.weight }};
            color: {{ config.fonts.body.color }};
            line-height: {{ config.fonts.body.line_height }};
            flex: 1;
            overflow: hidden;
            text-align: justify;
            white-space: pre-wrap;
        }

        .footer {
            margin-top: {{ config.spacing.footer_margin_top }}px;
            text-align: center;
            font-size: 24px;
            color: {{ config.colors.secondary or '#888888' }};
        }

        {% block extra_css %}{% endblock %}
    </style>
</head>
<body>
    <div class="container">
        {% if title %}
        <h1 class="title">{{ title }}</h1>
        {% endif %}

        <div class="content">{{ content }}</div>

        {% if author %}
        <div class="footer">@{{ author }}</div>
        {% endif %}
    </div>

    {% block extra_html %}{% endblock %}
</body>
</html>
""",
                encoding="utf-8",
            )

        # 创建小红书默认模板
        xiaohongshu_template = self.template_dir / "xiaohongshu" / "minimal.html"
        xiaohongshu_template.parent.mkdir(parents=True, exist_ok=True)

        if not xiaohongshu_template.exists():
            xiaohongshu_template.write_text(
                """{% extends "base/layout.html" %}

{% block extra_css %}
<style>
    .container {
        background: linear-gradient(135deg, {{ config.colors.background }} 0%, #F0F0F0 100%);
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
    }

    .title {
        border-bottom: 3px solid {{ config.colors.primary }};
        padding-bottom: 30px;
    }

    .content {
        font-weight: 500;
    }

    .footer {
        font-weight: 600;
        color: {{ config.colors.primary }};
    }
</style>
{% endblock %}
""",
                encoding="utf-8",
            )

    def render_template(
        self,
        template_name: str,
        platform: str,
        title: str,
        content: str,
        config: Dict[str, Any],
        **options,
    ) -> str:
        """
        渲染 HTML 模板

        Args:
            template_name: 模板名称（如 "minimal"）
            platform: 平台名称（如 "xiaohongshu"）
            title: 标题
            content: 内容
            config: 平台配置
            **options: 额外选项（如 author, title_align 等）

        Returns:
            渲染后的 HTML 字符串
        """
        try:
            # 尝试加载平台特定模板
            template_path = f"{platform}/{template_name}.html"
            template = self.jinja_env.get_template(template_path)
        except Exception:
            try:
                # 如果平台模板不存在，使用基础模板
                template = self.jinja_env.get_template(f"base/layout.html")
            except Exception as e:
                # 如果基础模板也不存在，返回简单的 HTML
                return self._render_simple_html(title, content, config, **options)

        # 渲染模板
        html = template.render(
            title=title,
            content=content,
            config=config,
            **options,
        )

        # 替换本地字体为系统字体（用于HTML预览）
        # 这不会影响最终图片渲染，因为Playwright会加载本地字体
        html = self._replace_fonts_with_system_fonts(html)

        return html

    def _render_simple_html(
        self,
        title: str,
        content: str,
        config: Dict[str, Any],
        **options,
    ) -> str:
        """渲染简单的 HTML（当模板不存在时）"""
        width = config.get("width", 1080)
        height = config.get("height", 1920)
        bg_color = config.get("colors", {}).get("background", "#FAFAFA")
        title_color = config.get("fonts", {}).get("title", {}).get("color", "#333333")
        title_size = config.get("fonts", {}).get("title", {}).get("size", 48)
        body_color = config.get("fonts", {}).get("body", {}).get("color", "#666666")
        body_size = config.get("fonts", {}).get("body", {}).get("size", 32)

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: "NotoSansSC", sans-serif;
            background-color: {bg_color};
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }}
        .container {{
            width: {width}px;
            height: {height}px;
            background-color: {bg_color};
            padding: 120px 80px;
            display: flex;
            flex-direction: column;
        }}
        .title {{
            font-size: {title_size}px;
            font-weight: bold;
            color: {title_color};
            line-height: 1.4;
            margin-bottom: 60px;
            text-align: center;
        }}
        .content {{
            font-size: {body_size}px;
            color: {body_color};
            line-height: 1.6;
            flex: 1;
            text-align: justify;
            white-space: pre-wrap;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1 class="title">{title}</h1>
        <div class="content">{content}</div>
    </div>
</body>
</html>
"""
        return html

    async def html_to_png(
        self,
        html: str,
        output_path: str,
        width: int = 1080,
        height: int = 1920,
    ) -> str:
        """
        将 HTML 转换为 PNG

        Args:
            html: HTML 字符串
            output_path: 输出文件路径
            width: 视口宽度
            height: 视口高度

        Returns:
            图片文件路径
        """
        async with async_playwright() as p:
            # 启动浏览器，启用字体渲染
            browser = await p.chromium.launch(
                args=[
                    '--font-render-hinting=none',
                    '--disable-font-subpixel-positioning',
                ]
            )

            try:
                # 创建新页面
                page = await browser.new_page()

                # 设置视口大小
                await page.set_viewport_size({"width": width, "height": height})

                # 设置 HTML 内容
                await page.set_content(html, wait_until="networkidle")

                # 等待字体加载
                await page.wait_for_timeout(2000)

                # 截图
                output_file = Path(output_path)
                output_file.parent.mkdir(parents=True, exist_ok=True)

                await page.screenshot(path=str(output_file), full_page=False)

                return str(output_file)

            finally:
                await browser.close()

    def escape_html(self, text: str) -> str:
        """转义 HTML 特殊字符"""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;")
        )

    def _replace_fonts_with_system_fonts(self, html: str) -> str:
        """
        将HTML中的自定义字体替换为系统字体

        这样做是为了让HTML预览在iframe中能正常显示
        最终图片渲染时Playwright会加载本地字体，所以不影响最终效果
        """
        import re

        # 字体映射：将自定义字体替换为类似的系统字体
        font_mappings = {
            "NotoSansSC": "PingFang SC, Microsoft YaHei, sans-serif",
            "SourceHanSerifSC": "PingFang SC, Songti SC, serif",
            "NotoSerifSC": "PingFang SC, Songti SC, serif",
        }

        # 替换 font-family 声明中的自定义字体
        for custom_font, system_font in font_mappings.items():
            # 匹配 font-family: "CustomFont" 或 font-family: CustomFont
            html = re.sub(
                rf'font-family:\s*["\']?{custom_font}["\']?',
                f'font-family: {system_font}',
                html
            )
            # 同时处理有fallback的情况
            html = re.sub(
                rf'font-family:\s*["\']?{custom_font}["\']?,\s*',
                f'font-family: {system_font}, ',
                html
            )

        return html
