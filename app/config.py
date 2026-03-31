"""
配置管理系统

支持从YAML文件加载配置，并支持环境变量替换
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv


# 加载环境变量
load_dotenv()


def _substitute_env(value: str) -> str:
    """替换字符串中的环境变量 ${VAR_NAME}"""
    if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
        env_var = value[2:-1]
        default_value = None
        if ':-' in env_var:
            env_var, default_value = env_var.split(':-', 1)

        return os.getenv(env_var, default_value or '')
    return value


def _substitute_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """递归替换字典中的环境变量"""
    result = {}
    for key, value in data.items():
        if isinstance(value, dict):
            result[key] = _substitute_dict(value)
        elif isinstance(value, str):
            result[key] = _substitute_env(value)
        else:
            result[key] = value
    return result


@dataclass
class Settings:
    """应用配置"""

    # 数据库配置
    database_url: str = "sqlite://./data/database.db"

    # LLM配置
    llm_default_provider: str = "qianwen"
    llm_providers: Dict[str, Any] = field(default_factory=dict)

    # 调度器配置
    scheduler_timezone: str = "Asia/Shanghai"
    scheduler_max_workers: int = 3

    # 日志配置
    log_level: str = "INFO"
    log_file: str = "data/logs/app.log"

    # 目录配置
    data_dir: str = "data"
    content_dir: str = "data/content"
    drafts_dir: str = "data/drafts"
    logs_dir: str = "data/logs"

    # 配置文件路径
    config_dir: str = "config"
    agents_config_dir: str = "config/agents"
    skills_dir: str = "app/skills/skills"

    @classmethod
    def load_from_yaml(cls, config_path: str = "config/settings.yaml") -> "Settings":
        """从YAML文件加载配置"""
        config_file = Path(config_path)
        if not config_file.exists():
            logger = __import__('logging').getLogger(__name__)
            logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
            return cls()

        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        # 替换环境变量
        config_data = _substitute_dict(config_data)

        # 映射配置到Settings
        settings = cls()

        if 'database' in config_data:
            settings.database_url = config_data['database'].get('url', settings.database_url)

        if 'llm' in config_data:
            settings.llm_default_provider = config_data['llm'].get('default_provider', settings.llm_default_provider)
            settings.llm_providers = config_data['llm'].get('providers', {})

        if 'scheduler' in config_data:
            scheduler_config = config_data['scheduler']
            settings.scheduler_timezone = scheduler_config.get('timezone', settings.scheduler_timezone)
            settings.scheduler_max_workers = scheduler_config.get('max_workers', settings.scheduler_max_workers)

        if 'logging' in config_data:
            logging_config = config_data['logging']
            settings.log_level = logging_config.get('level', settings.log_level)
            settings.log_file = logging_config.get('file', settings.log_file)

        return settings

    def get_llm_provider_config(self, provider_name: Optional[str] = None) -> Dict[str, Any]:
        """获取LLM提供商配置"""
        provider_name = provider_name or self.llm_default_provider
        return self.llm_providers.get(provider_name, {})


# 全局配置实例
settings = Settings.load_from_yaml()
