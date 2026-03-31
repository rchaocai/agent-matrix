"""
图文内容渲染引擎 - 基础框架
将文本内容渲染为平台图文卡片
"""

from .render import RenderEngine
from .template_manager import TemplateManager
from .platform_adapter import PlatformAdapter
from .content_splitter import ContentSplitter

__all__ = [
    "RenderEngine",
    "TemplateManager",
    "PlatformAdapter",
    "ContentSplitter",
]
