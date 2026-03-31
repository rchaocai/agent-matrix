"""
敏感词检测脚本
"""

import os
import re
import json
import argparse
from typing import Dict, List, Any, Set
from pathlib import Path


class SensitiveWordChecker:
    """敏感词检测器"""

    def __init__(self, strictness: str = "medium"):
        self.strictness = strictness
        self.sensitive_words = {}
        self.load_sensitive_words()

    def load_sensitive_words(self):
        """加载敏感词库"""
        assets_dir = Path(__file__).parent.parent / "assets" / "sensitive_words"

        # 类别映射
        categories = {
            'politics': 'politics.txt',
            'porn': 'porn.txt',
            'violence': 'violence.txt',
            'spam': 'spam.txt',
            'illegal': 'illegal.txt'
        }

        for category, filename in categories.items():
            file_path = assets_dir / filename
            words = set()

            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        word = line.strip()
                        if word and not word.startswith('#'):
                            words.add(word)

            self.sensitive_words[category] = words

    def check_phone_number(self, text: str) -> List[str]:
        """检测电话号码"""
        patterns = [
            r'1[3-9]\d{9}',  # 手机号
            r'\d{3,4}-\d{7,8}',  # 座机
            r'400-\d{7}',  # 400电话
        ]

        found = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            found.extend(matches)

        return found

    def check_email(self, text: str) -> List[str]:
        """检测邮箱"""
        pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        return re.findall(pattern, text)

    def check_wechat_qq(self, text: str) -> List[str]:
        """检测微信号、QQ号"""
        patterns = [
            r'微信[：:]\s*[a-zA-Z0-9_-]+',
            r'wx[：:]\s*[a-zA-Z0-9_-]+',
            r'QQ[：:]\s*\d{5,11}',
            r'qq[：:]\s*\d{5,11}',
        ]

        found = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            found.extend(matches)

        return found

    def check_url(self, text: str) -> List[str]:
        """检测URL"""
        pattern = r'https?://[^\s]+'
        return re.findall(pattern, text)

    def check_sensitive_words(
        self,
        text: str,
        categories: List[str] = None,
        custom_words: Set[str] = None
    ) -> Dict[str, Any]:
        """
        检测敏感词

        Args:
            text: 待检测文本
            categories: 检测类别
            custom_words: 自定义敏感词

        Returns:
            检测结果
        """
        if categories is None or 'all' in categories:
            categories = list(self.sensitive_words.keys())

        detected = {}
        all_found_words = []

        for category in categories:
            if category not in self.sensitive_words:
                continue

            words = self.sensitive_words[category]
            found_words = []

            # 检查每个敏感词
            for word in words:
                if word in text:
                    found_words.append(word)
                    all_found_words.append(word)

            if found_words:
                detected[category] = found_words

        # 检查自定义敏感词
        if custom_words:
            custom_found = []
            for word in custom_words:
                if word in text:
                    custom_found.append(word)
                    all_found_words.append(word)

            if custom_found:
                detected['custom'] = custom_found

        # 计算风险等级
        risk_level = self.calculate_risk_level(detected, len(text))

        return {
            'detected': detected,
            'total_words': len(all_found_words),
            'risk_level': risk_level,
            'is_safe': risk_level == 'low'
        }

    def calculate_risk_level(self, detected: Dict[str, List[str]], text_length: int) -> str:
        """计算风险等级"""
        total_detected = sum(len(words) for words in detected.values())

        if total_detected == 0:
            return 'low'
        elif total_detected <= 3:
            return 'medium'
        else:
            return 'high'

    def full_check(
        self,
        content: str,
        categories: List[str] = None,
        custom_words: str = None
    ) -> Dict[str, Any]:
        """
        完整检测

        Args:
            content: 待检测内容
            categories: 检测类别
            custom_words: 自定义敏感词（逗号分隔）

        Returns:
            检测结果
        """
        result = {
            'content_length': len(content),
            'is_safe': True,
            'risk_level': 'low',
            'detected_items': {},
            'categories_checked': []
        }

        # 1. 敏感词检测
        custom_set = set(custom_words.split(',')) if custom_words else None
        word_result = self.check_sensitive_words(content, categories, custom_set)

        if word_result['detected']:
            result['detected_items']['sensitive_words'] = word_result['detected']
            result['categories_checked'].extend(word_result['detected'].keys())

        # 2. 联系方式检测
        phones = self.check_phone_number(content)
        if phones:
            result['detected_items']['phone_numbers'] = phones

        emails = self.check_email(content)
        if emails:
            result['detected_items']['emails'] = emails

        wechat_qq = self.check_wechat_qq(content)
        if wechat_qq:
            result['detected_items']['social_accounts'] = wechat_qq

        # 3. URL检测
        urls = self.check_url(content)
        if urls:
            result['detected_items']['urls'] = urls

        # 4. 计算总体风险
        total_items = sum(len(items) for items in result['detected_items'].values())
        if total_items > 0 or word_result['total_words'] > 0:
            result['is_safe'] = False
            result['risk_level'] = word_result['risk_level']
            result['confidence'] = 0.9 if total_items > 5 else 0.7
        else:
            result['confidence'] = 0.95

        return result


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='敏感词检测工具')
    parser.add_argument('--content', required=True, help='待检测内容')
    parser.add_argument('--categories', default='all',
                       help='检测类别，逗号分隔（politics,porn,violence,spam,illegal）')
    parser.add_argument('--strictness', default='medium',
                       choices=['low', 'medium', 'high'],
                       help='严格程度')
    parser.add_argument('--custom-words', help='自定义敏感词，逗号分隔')

    args = parser.parse_args()

    # 创建检测器
    checker = SensitiveWordChecker(strictness=args.strictness)

    # 执行检测
    categories = args.categories.split(',') if args.categories != 'all' else None
    result = checker.full_check(
        content=args.content,
        categories=categories,
        custom_words=args.custom_words
    )

    # 输出JSON结果
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
