"""
平台适配器 - 处理不同平台的排版规则
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List


class PlatformAdapter:
    """平台适配器 - 处理不同平台的排版规则"""

    def __init__(self, config_dir: str = "config/platforms"):
        self.config_dir = Path(config_dir)
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._load_configs()

    def _load_configs(self):
        """加载所有平台配置文件"""
        if not self.config_dir.exists():
            # 如果配置目录不存在，使用默认配置
            self._configs = self._get_default_configs()
            return

        for config_file in self.config_dir.glob("*.yaml"):
            platform_name = config_file.stem
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    self._configs[platform_name] = yaml.safe_load(f)
            except Exception as e:
                print(f"Warning: Failed to load config for {platform_name}: {e}")

        # 如果没有加载到任何配置，使用默认配置
        if not self._configs:
            self._configs = self._get_default_configs()

    def _get_default_configs(self) -> Dict[str, Dict[str, Any]]:
        """获取默认平台配置"""
        return {
            "xiaohongshu": {
                "width": 1080,
                "height": 1920,
                "max_length": 500,
                "dpi": 150,
                "fonts": {
                    "title": {
                        "family": "SourceHanSerifSC, NotoSansSC",
                        "size": 64,
                        "weight": "bold",
                        "color": "#333333",
                        "line_height": 1.4,
                    },
                    "body": {
                        "family": "NotoSansSC",
                        "size": 40,
                        "weight": "normal",
                        "color": "#666666",
                        "line_height": 1.6,
                    },
                },
                "colors": {
                    "background": "#FAFAFA",
                    "primary": "#FF2442",
                    "secondary": "#888888",
                    "text": "#333333",
                    "accent": "#FFB800",
                },
                "spacing": {
                    "padding_top": 120,
                    "padding_bottom": 120,
                    "padding_left": 80,
                    "padding_right": 80,
                    "content_margin_bottom": 60,
                    "footer_margin_top": 80,
                },
            },
            "douyin": {
                "width": 1080,
                "height": 1920,
                "max_length": 300,
                "dpi": 150,
                "fonts": {
                    "title": {
                        "family": "SourceHanSerifSC, NotoSansSC",
                        "size": 72,
                        "weight": "bold",
                        "color": "#FFFFFF",
                        "line_height": 1.4,
                    },
                    "body": {
                        "family": "NotoSansSC",
                        "size": 44,
                        "weight": "normal",
                        "color": "#E0E0E0",
                        "line_height": 1.6,
                    },
                },
                "colors": {
                    "background": "#1A1A1A",
                    "primary": "#FF0050",
                    "secondary": "#888888",
                    "text": "#FFFFFF",
                    "accent": "#00E5FF",
                },
                "spacing": {
                    "padding_top": 140,
                    "padding_bottom": 140,
                    "padding_left": 90,
                    "padding_right": 90,
                    "content_margin_bottom": 70,
                    "footer_margin_top": 90,
                },
            },
        }

    def get_config(self, platform: str) -> Dict[str, Any]:
        """
        获取平台配置

        Args:
            platform: 平台名称

        Returns:
            平台配置字典
        """
        if platform not in self._configs:
            print(f"Warning: Platform '{platform}' not found, using 'xiaohongshu' as default")
            platform = "xiaohongshu"

        return self._configs.get(platform, self._configs["xiaohongshu"])

    def get_supported_platforms(self) -> list:
        """获取支持的平台列表"""
        return list(self._configs.keys())

    def validate_platform(self, platform: str) -> bool:
        """验证平台是否支持"""
        return platform in self._configs

    def get_color_scheme(self, platform: str, template: str, scheme_name: str) -> Optional[Dict[str, Any]]:
        """
        获取指定模板的配色方案

        Args:
            platform: 平台名称
            template: 模板名称
            scheme_name: 配色方案名称

        Returns:
            配色配置字典，如果未找到返回 None
        """
        config = self.get_config(platform)
        templates = config.get('templates', {})
        template_config = templates.get(template, {})
        color_schemes = template_config.get('color_schemes', [])

        for scheme in color_schemes:
            if scheme.get('name') == scheme_name:
                return {
                    'background': scheme.get('background'),
                    'primary': scheme.get('primary'),
                    'secondary': scheme.get('secondary', config['colors'].get('secondary')),
                    'text': scheme.get('text', config['colors'].get('text')),
                    'accent': scheme.get('accent', config['colors'].get('accent')),
                }
        return None

    def get_font_scheme(self, platform: str, template: str, scheme_name: str) -> Optional[Dict[str, Any]]:
        """
        获取指定模板的字体方案

        Args:
            platform: 平台名称
            template: 模板名称
            scheme_name: 字体方案名称

        Returns:
            字体配置字典，如果未找到返回 None
        """
        config = self.get_config(platform)
        templates = config.get('templates', {})
        template_config = templates.get(template, {})
        font_schemes = template_config.get('font_schemes', [])

        for scheme in font_schemes:
            if scheme.get('name') == scheme_name:
                return {
                    'title_font': scheme.get('title_font', '').replace('"', ''),
                    'body_font': scheme.get('body_font', '').replace('"', ''),
                }
        return None

    def get_all_color_schemes(self, platform: str) -> Dict[str, List[Dict]]:
        """
        获取平台所有模板的配色方案

        Args:
            platform: 平台名称

        Returns:
            {template_name: [scheme1, scheme2, ...]}
        """
        config = self.get_config(platform)
        templates = config.get('templates', {})

        result = {}
        for template_name, template_config in templates.items():
            if 'color_schemes' in template_config:
                result[template_name] = template_config['color_schemes']

        return result

    def get_all_font_schemes(self, platform: str) -> Dict[str, List[Dict]]:
        """
        获取平台所有模板的字体方案

        Args:
            platform: 平台名称

        Returns:
            {template_name: [scheme1, scheme2, ...]}
        """
        config = self.get_config(platform)
        templates = config.get('templates', {})

        result = {}
        for template_name, template_config in templates.items():
            if 'font_schemes' in template_config:
                result[template_name] = template_config['font_schemes']

        return result
