"""
内容质量评分脚本
"""

import re
import json
import argparse
from typing import Dict, List, Any
from collections import Counter


class ContentQualityScorer:
    """内容质量评分器"""

    def __init__(self, platform: str = "general"):
        self.platform = platform

    def score_readability(self, content: str) -> Dict[str, Any]:
        """评分可读性"""
        issues = []
        score = 100

        # 移除多余空白
        content_clean = re.sub(r'\s+', ' ', content.strip())

        # 检查句子长度
        sentences = re.split(r'[。！？.!?]', content_clean)
        sentences = [s.strip() for s in sentences if s.strip()]

        if sentences:
            avg_length = sum(len(s) for s in sentences) / len(sentences)

            if avg_length > 50:
                issues.append("平均句子过长（建议15-25字）")
                score -= 15
            elif avg_length < 10:
                issues.append("句子过短（可能影响表达）")
                score -= 10

            # 检查过长句子
            long_sentences = [s for s in sentences if len(s) > 50]
            if len(long_sentences) > len(sentences) * 0.3:
                issues.append(f"有{len(long_sentences)}个长句（超过30%）")
                score -= 10

        # 检查段落结构
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        if len(paragraphs) < 2:
            issues.append("段落过少（建议分段）")
            score -= 10
        elif len(paragraphs) > 10:
            issues.append("段落过多（建议精简）")
            score -= 5

        # 检查标点符号
        punctuation_ratio = len(re.findall(r'[，。！？、；：""''（）《》]', content)) / max(len(content), 1)
        if punctuation_ratio < 0.05:
            issues.append("标点符号使用过少")
            score -= 10

        # 检查换行
        if '\n' not in content:
            issues.append("缺少换行（建议分段）")
            score -= 10

        return {
            'score': max(0, score),
            'issues': issues,
            'sentence_count': len(sentences) if sentences else 0,
            'paragraph_count': len(paragraphs),
            'avg_sentence_length': avg_length if sentences else 0
        }

    def score_completeness(self, content: str, has_title: bool = False) -> Dict[str, Any]:
        """评分完整性"""
        missing = []
        score = 100

        # 检查标题
        if not has_title:
            missing.append("缺少标题")
            score -= 20

        # 检查内容长度
        content_length = len(content.strip())
        if content_length < 50:
            missing.append("内容过短")
            score -= 30
        elif content_length > 2000:
            missing.append("内容过长（可能影响阅读）")
            score -= 10

        # 检查开头
        first_para = content.strip().split('\n\n')[0] if content else ''
        if len(first_para) < 10:
            missing.append("缺少有效开头")
            score -= 15

        # 检查结尾
        last_para = content.strip().split('\n\n')[-1] if content else ''
        if len(last_para) < 10:
            missing.append("缺少有效结尾")
            score -= 15

        # 检查逻辑连贯性
        # 简化检查：看是否有明显的中断
        if content.count('...') > 3:
            missing.append("内容不完整（存在过多省略号）")
            score -= 10

        return {
            'score': max(0, score),
            'missing_elements': missing,
            'content_length': content_length,
            'has_title': has_title
        }

    def score_attractiveness(self, content: str) -> Dict[str, Any]:
        """评分吸引力"""
        suggestions = []
        score = 100

        # 检查emoji使用（针对小红书等平台）
        emoji_count = len(re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', content))

        if self.platform == 'xiaohongshu':
            if emoji_count == 0:
                suggestions.append("建议添加emoji（小红书用户喜欢）")
                score -= 10
            elif emoji_count > 10:
                suggestions.append("emoji过多（建议3-5个）")
                score -= 5

        # 检查提问
        questions = len(re.findall(r'[?？]', content))
        if questions == 0:
            suggestions.append("建议添加提问以增加互动")
            score -= 10

        # 检查感叹号
        exclamations = len(re.findall(r'[!！]', content))
        if exclamations > 5:
            suggestions.append("感叹号过多（可能影响专业感）")
            score -= 5

        # 检查关键词
        engaging_words = ['必看', '分享', '干货', '建议收藏', '实用', '教程', '技巧', '秘诀', '方法']
        found_engaging = sum(1 for word in engaging_words if word in content)

        if found_engaging == 0:
            suggestions.append("建议增加吸引性词汇（分享、干货、教程等）")
            score -= 10
        elif found_engaging >= 3:
            score += 5  # 加分项

        # 检查数字使用
        numbers = len(re.findall(r'\d+', content))
        if numbers == 0:
            suggestions.append("建议添加具体数字（增加可信度）")
            score -= 5

        return {
            'score': max(0, min(100, score)),
            'suggestions': suggestions,
            'emoji_count': emoji_count,
            'question_count': questions,
            'engaging_words': found_engaging
        }

    def score_originality(self, content: str) -> Dict[str, Any]:
        """评分原创性（简化版）"""
        score = 100
        warnings = []

        # 检查常见模板化表达
        templates = [
            '本文仅供参考',
            '来源于网络',
            '如有侵权请联系删除',
            '未经授权不得转载'
        ]

        found_templates = [t for t in templates if t in content]
        if found_templates:
            warnings.append(f"包含模板化表达: {', '.join(found_templates)}")
            score -= 10

        # 检查重复词
        words = re.findall(r'[\w]+', content)
        if words:
            word_freq = Counter(words)
            max_freq = max(word_freq.values())
            if max_freq > len(words) * 0.1:
                warnings.append(f"词汇重复率过高（最高重复{max_freq}次）")
                score -= 15

        return {
            'score': max(0, score),
            'warnings': warnings
        }

    def full_score(
        self,
        content: str,
        title: str = None,
        dimensions: List[str] = None,
        min_score: int = 60,
        weights: Dict[str, int] = None
    ) -> Dict[str, Any]:
        """
        完整评分

        Args:
            content: 待评分内容
            title: 标题（可选）
            dimensions: 评分维度
            min_score: 最低合格分数
            weights: 各维度权重

        Returns:
            评分结果
        """
        if dimensions is None:
            dimensions = ['readability', 'completeness', 'attractiveness']
        
        if weights is None:
            weights = {'readability': 30, 'completeness': 40, 'attractiveness': 30}

        result = {
            'content_length': len(content),
            'platform': self.platform,
            'dimensions': {},
            'overall_score': 0,
            'is_recommended': False,
            'is_qualified': False
        }

        scores = []

        # 可读性评分
        if 'readability' in dimensions:
            readability = self.score_readability(content)
            result['dimensions']['readability'] = readability
            weight = weights.get('readability', 30)
            scores.append(readability['score'] * weight / 100)

        # 完整性评分
        if 'completeness' in dimensions:
            completeness = self.score_completeness(content, has_title=bool(title))
            result['dimensions']['completeness'] = completeness
            weight = weights.get('completeness', 40)
            scores.append(completeness['score'] * weight / 100)

        # 吸引力评分
        if 'attractiveness' in dimensions:
            attractiveness = self.score_attractiveness(content)
            result['dimensions']['attractiveness'] = attractiveness
            weight = weights.get('attractiveness', 30)
            scores.append(attractiveness['score'] * weight / 100)

        # 原创性评分
        if 'originality' in dimensions:
            originality = self.score_originality(content)
            result['dimensions']['originality'] = originality
            weight = weights.get('originality', 0)
            scores.append(originality['score'] * weight / 100)

        # 计算总体评分（加权平均）
        if scores:
            result['overall_score'] = int(sum(scores))
        else:
            result['overall_score'] = 0

        # 判断是否推荐
        result['is_recommended'] = result['overall_score'] >= 75
        result['is_qualified'] = result['overall_score'] >= min_score

        # 生成建议
        suggestions = []
        for dim_name, dim_data in result['dimensions'].items():
            if 'issues' in dim_data:
                suggestions.extend(dim_data['issues'])
            if 'suggestions' in dim_data:
                suggestions.extend(dim_data['suggestions'])
            if 'warnings' in dim_data:
                suggestions.extend(dim_data['warnings'])

        result['suggestions'] = list(set(suggestions)) if suggestions else []

        return result


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='内容质量评分工具')
    parser.add_argument('--content', required=True, help='待评分内容')
    parser.add_argument('--title', help='内容标题')
    parser.add_argument('--platform', default='general',
                       choices=['xiaohongshu', 'douyin', 'general'],
                       help='目标平台')
    parser.add_argument('--dimensions', default='readability,completeness,attractiveness',
                       help='评分维度，逗号分隔')
    parser.add_argument('--min_score', type=int, default=60,
                       help='最低合格分数')

    args = parser.parse_args()

    # 创建评分器
    scorer = ContentQualityScorer(platform=args.platform)

    # 执行评分
    dimensions = args.dimensions.split(',') if args.dimensions else []
    result = scorer.full_score(
        content=args.content,
        title=args.title,
        dimensions=dimensions,
        min_score=args.min_score
    )

    # 输出JSON结果
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
