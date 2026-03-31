"""
图文内容渲染引擎 - 主渲染脚本
"""

import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import aiofiles
import copy

from .platform_adapter import PlatformAdapter
from .template_manager import TemplateManager
from .content_splitter import ContentSplitter


class RenderEngine:
    """图文内容渲染引擎"""

    def __init__(
        self,
        template_dir: Optional[str] = None,
        config_dir: Optional[str] = None,
    ):
        """
        初始化渲染引擎

        Args:
            template_dir: 模板目录
            config_dir: 平台配置目录
        """
        self.platform_adapter = PlatformAdapter(config_dir or "config/platforms")
        self.template_manager = TemplateManager(
            template_dir or "app/skills/skills/generation/render/assets/templates"
        )
        self.content_splitter = ContentSplitter()

    async def render(
        self,
        title: str,
        content: str,
        platform: str = "xiaohongshu",
        template: str = "minimal",
        max_length: Optional[int] = None,
        split_long: bool = True,
        output_dir: str = "data/images/drafts",
        color_scheme: Optional[str] = None,
        font_scheme: Optional[str] = None,
        **options,
    ) -> Dict[str, Any]:
        """
        渲染文本内容为图片

        Args:
            title: 标题
            content: 正文内容
            platform: 目标平台
            template: 模板名称
            max_length: 单张最大字数
            split_long: 是否自动分割长文
            output_dir: 输出目录（默认 data/images/drafts）
            color_scheme: 配色方案名称
            font_scheme: 字体方案名称
            **options: 额外选项（如 author, title_align 等）

        Returns:
            {
                "rendered_images": ["path1", "path2"],
                "total_pages": 2,
                "platform": "xiaohongshu",
                "template": "minimal"
            }
        """
        # 1. 获取平台配置
        config = self.platform_adapter.get_config(platform)

        # 2. 应用配色方案（如果指定）
        if color_scheme:
            scheme_colors = self.platform_adapter.get_color_scheme(
                platform, template, color_scheme
            )
            if scheme_colors:
                # 深拷贝配置以避免修改原始配置
                config = copy.deepcopy(config)
                # 合并配色方案，保留原有的其他配置
                config['colors'] = {**config['colors'], **scheme_colors}

        # 3. 应用字体方案（如果指定）
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"字体方案参数: font_scheme={font_scheme}")
        
        if font_scheme:
            scheme_fonts = self.platform_adapter.get_font_scheme(
                platform, template, font_scheme
            )
            logger.info(f"获取到的字体方案: {scheme_fonts}")
            if scheme_fonts:
                if config is self.platform_adapter.get_config(platform):
                    config = copy.deepcopy(config)
                # 应用字体方案到 fonts 配置
                if 'fonts' not in config:
                    config['fonts'] = {}
                if scheme_fonts.get('title_font'):
                    if 'title' not in config['fonts']:
                        config['fonts']['title'] = {}
                    config['fonts']['title']['family'] = scheme_fonts['title_font']
                if scheme_fonts.get('body_font'):
                    if 'body' not in config['fonts']:
                        config['fonts']['body'] = {}
                    config['fonts']['body']['family'] = scheme_fonts['body_font']
                logger.info(f"应用字体方案后: title_font={config['fonts'].get('title', {}).get('family')}, body_font={config['fonts'].get('body', {}).get('family')}")

        # 3. 设置默认值
        if max_length is None:
            max_length = config.get("max_length", 500)

        # 4. 分割内容（如果需要）
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"渲染参数: split_long={split_long}, max_length={max_length}, content_length={len(content)}")
        
        if split_long and len(content) > max_length:
            pages_with_titles = self.content_splitter.split_with_continuation(
                content, max_length, title
            )
            logger.info(f"内容分割为 {len(pages_with_titles)} 页")
        else:
            pages_with_titles = [(content, title)]
            logger.info(f"内容不分割: split_long={split_long}, content_length={len(content)}, max_length={max_length}")

        # 5. 批量渲染
        rendered_images = []
        width = config.get("width", 1080)
        height = config.get("height", 1920)

        for i, (page_content, page_title) in enumerate(pages_with_titles):
            # 第一张图显示标题，后续图片不显示标题
            display_title = page_title if i == 0 else ""

            # 渲染 HTML
            html = self.template_manager.render_template(
                template_name=template,
                platform=platform,
                title=display_title,
                content=page_content,
                config=config,
                **options,
            )
            
            # 检查 HTML 中的字体设置
            if 'font-family' in html:
                import re
                title_font_match = re.search(r'\.title\s*{[^}]*font-family:\s*([^;]+)', html)
                body_font_match = re.search(r'\.content\s*{[^}]*font-family:\s*([^;]+)', html)
                logger.info(f"HTML中的字体设置 - title: {title_font_match.group(1) if title_font_match else '未找到'}, body: {body_font_match.group(1) if body_font_match else '未找到'}")

            # 生成输出文件路径
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{platform}_{template}_{timestamp}_{i + 1}.png"
            output_path = Path(output_dir) / datetime.now().strftime("%Y%m%d") / filename
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # 转换为 PNG
            image_path = await self.template_manager.html_to_png(
                html=html,
                output_path=str(output_path),
                width=width,
                height=height,
            )

            rendered_images.append(str(image_path))

        return {
            "rendered_images": rendered_images,
            "total_pages": len(rendered_images),
            "platform": platform,
            "template": template,
        }

    def render_sync(
        self,
        title: str,
        content: str,
        platform: str = "xiaohongshu",
        template: str = "minimal",
        max_length: Optional[int] = None,
        split_long: bool = True,
        output_dir: str = "data/images/drafts",
        **options,
    ) -> Dict[str, Any]:
        """
        同步版本的渲染方法

        Args:
            同 render()

        Returns:
            同 render()
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running event loop
            loop = None

        if loop is not None:
            # We're in an async context, create a task
            import concurrent.futures
            import threading

            result = []
            exception = []

            def run_in_new_loop():
                try:
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    task = self.render(
                        title=title,
                        content=content,
                        platform=platform,
                        template=template,
                        max_length=max_length,
                        split_long=split_long,
                        output_dir=output_dir,
                        **options,
                    )
                    result.append(new_loop.run_until_complete(task))
                    new_loop.close()
                except Exception as e:
                    exception.append(e)

            thread = threading.Thread(target=run_in_new_loop)
            thread.start()
            thread.join()

            if exception:
                raise exception[0]
            return result[0]
        else:
            # No running loop, use asyncio.run
            return asyncio.run(self.render(
                title=title,
                content=content,
                platform=platform,
                template=template,
                max_length=max_length,
                split_long=split_long,
                output_dir=output_dir,
                **options,
            ))

    async def render_batch(
        self,
        items: List[Dict[str, str]],
        platform: str = "xiaohongshu",
        template: str = "minimal",
        max_length: Optional[int] = None,
        split_long: bool = True,
        output_dir: str = "data/images/drafts",
        **options,
    ) -> List[Dict[str, Any]]:
        """
        批量渲染多个内容

        Args:
            items: [{title: "...", content: "..."}, ...]
            其他参数同 render()

        Returns:
            [result1, result2, ...]
        """
        tasks = []

        for item in items:
            task = self.render(
                title=item.get("title", ""),
                content=item.get("content", ""),
                platform=platform,
                template=template,
                max_length=max_length,
                split_long=split_long,
                output_dir=output_dir,
                **options,
            )
            tasks.append(task)

        # 并发执行所有渲染任务
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Error rendering item {i}: {result}")
                final_results.append({
                    "error": str(result),
                    "rendered_images": [],
                    "total_pages": 0,
                })
            else:
                final_results.append(result)

        return final_results

    def get_supported_platforms(self) -> List[str]:
        """获取支持的平台列表"""
        return self.platform_adapter.get_supported_platforms()

    def validate_platform(self, platform: str) -> bool:
        """验证平台是否支持"""
        return self.platform_adapter.validate_platform(platform)


# 便捷函数
async def render_text_to_image(
    title: str,
    content: str,
    platform: str = "xiaohongshu",
    template: str = "minimal",
    **options,
) -> Dict[str, Any]:
    """
    便捷函数：将文本渲染为图片

    Args:
        title: 标题
        content: 内容
        platform: 平台
        template: 模板
        **options: 额外选项

    Returns:
        渲染结果
    """
    engine = RenderEngine()
    return await engine.render(
        title=title,
        content=content,
        platform=platform,
        template=template,
        **options,
    )


def render_text_to_image_sync(
    title: str,
    content: str,
    platform: str = "xiaohongshu",
    template: str = "minimal",
    **options,
) -> Dict[str, Any]:
    """
    便捷函数（同步版本）：将文本渲染为图片

    Args:
        title: 标题
        content: 内容
        platform: 平台
        template: 模板
        **options: 额外选项

    Returns:
        渲染结果
    """
    engine = RenderEngine()
    return engine.render_sync(
        title=title,
        content=content,
        platform=platform,
        template=template,
        **options,
    )
