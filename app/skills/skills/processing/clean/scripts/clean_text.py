"""
文本清洗脚本
"""

import re
import json
import argparse
from typing import Dict, Any
from html import unescape


def clean_html(text: str) -> str:
    """
    移除HTML标签

    Args:
        text: 包含HTML的文本

    Returns:
        清洗后的文本
    """
    # 移除script和style标签及其内容
    text = re.sub(r'<script[^>]*?>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*?>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)

    # 移除HTML标签
    text = re.sub(r'<[^>]+>', '', text)

    # 解码HTML实体
    text = unescape(text)

    return text


def normalize_whitespace(text: str) -> str:
    """
    标准化空白字符

    Args:
        text: 原始文本

    Returns:
        标准化后的文本
    """
    # 替换多个空格为单个空格
    text = re.sub(r' +', ' ', text)

    # 替换多个换行为单个换行
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)

    # 移除行首行尾空白
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)

    return text.strip()


def remove_special_chars(text: str, preserve_urls: bool = False) -> str:
    """
    移除特殊字符

    Args:
        text: 原始文本
        preserve_urls: 是否保留URL

    Returns:
        清理后的文本
    """
    if preserve_urls:
        # 先保护URL
        urls = re.findall(r'https?://\S+', text)
        for i, url in enumerate(urls):
            text = text.replace(url, f'__URL_{i}__')

    # 移除控制字符（保留换行和制表符）
    text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)

    # 统一引号
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(''', "'").replace(''', "'")

    if preserve_urls:
        # 恢复URL
        for i, url in enumerate(urls):
            text = text.replace(f'__URL_{i}__', url)

    return text


def remove_duplicates(text: str) -> Dict[str, Any]:
    """
    移除重复段落

    Args:
        text: 原始文本

    Returns:
        清洗结果和统计信息
    """
    paragraphs = text.split('\n\n')
    seen = set()
    unique_paragraphs = []
    duplicates_count = 0

    for para in paragraphs:
        para_stripped = para.strip()
        if para_stripped and para_stripped not in seen:
            seen.add(para_stripped)
            unique_paragraphs.append(para)
        elif para_stripped:
            duplicates_count += 1

    return {
        'text': '\n\n'.join(unique_paragraphs),
        'duplicates_removed': duplicates_count
    }


def clean_text(
    input_text: str,
    remove_html: bool = True,
    min_length: int = 0,
    remove_duplicates: bool = False,
    preserve_urls: bool = False
) -> Dict[str, Any]:
    """
    完整的文本清洗流程

    Args:
        input_text: 输入文本
        remove_html: 是否移除HTML标签
        min_length: 最小内容长度
        remove_duplicates: 是否移除重复
        preserve_urls: 是否保留URL

    Returns:
        清洗结果
    """
    original_length = len(input_text)
    result = {
        'original_length': original_length,
        'cleaned_length': 0,
        'text': '',
        'removed_html': False,
        'removed_duplicates': False,
        'too_short': False
    }

    # 移除HTML
    if remove_html:
        input_text = clean_html(input_text)
        result['removed_html'] = True

    # 移除特殊字符
    input_text = remove_special_chars(input_text, preserve_urls)

    # 标准化空白
    input_text = normalize_whitespace(input_text)

    # 移除重复
    if remove_duplicates:
        dup_result = remove_duplicates(input_text)
        input_text = dup_result['text']
        result['removed_duplicates'] = dup_result['duplicates_removed'] > 0
        result['duplicates_count'] = dup_result['duplicates_removed']

    # 检查最小长度
    if min_length > 0 and len(input_text) < min_length:
        result['too_short'] = True
        result['text'] = ''
        return result

    result['text'] = input_text
    result['cleaned_length'] = len(input_text)

    return result


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='文本清洗工具')
    parser.add_argument('--input', required=True, help='输入文本')
    parser.add_argument('--remove-html', action='store_true', default=True,
                       help='移除HTML标签')
    parser.add_argument('--min-length', type=int, default=0,
                       help='最小内容长度')
    parser.add_argument('--remove-duplicates', action='store_true',
                       help='移除重复段落')
    parser.add_argument('--preserve-urls', action='store_true',
                       help='保留URL链接')

    args = parser.parse_args()

    # 执行清洗
    result = clean_text(
        input_text=args.input,
        remove_html=args.remove_html,
        min_length=args.min_length,
        remove_duplicates=args.remove_duplicates,
        preserve_urls=args.preserve_urls
    )

    # 输出JSON结果
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
