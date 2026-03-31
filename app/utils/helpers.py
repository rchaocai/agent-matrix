"""
工具函数模块
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional


def setup_logger(name: str, log_file: str, level: str = "INFO") -> logging.Logger:
    """
    设置日志记录器

    Args:
        name: 日志记录器名称
        log_file: 日志文件路径
        level: 日志级别

    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)

    # 确保日志目录存在
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # 设置日志级别
    logger.setLevel(getattr(logging, level))

    # 文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(getattr(logging, level))

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level))

    # 格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def ensure_dir(path: str) -> Path:
    """
    确保目录存在

    Args:
        path: 目录路径

    Returns:
        Path对象
    """
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_timestamp() -> str:
    """获取当前时间戳字符串"""
    return datetime.now().strftime('%Y%m%d_%H%M%S')


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除不合法字符

    Args:
        filename: 原始文件名

    Returns:
        清理后的文件名
    """
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename
