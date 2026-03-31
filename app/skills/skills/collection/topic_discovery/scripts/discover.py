"""
主题发现Skill - 基于爬虫数据源和LLM分析
"""
import asyncio
import feedparser
from typing import List, Dict, Optional
from datetime import datetime
import yaml
import logging
import sys
import json
import hashlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from app.core.hot_data_fetcher import HotDataFetcher
from app.core.llm_service import create_llm_service_from_env

logger = logging.getLogger(__name__)


class TopicDiscoverySkill:
    """主题发现技能"""
    
    def __init__(self):
        self.config = self._load_config()
        self.hot_fetcher = HotDataFetcher()
        self.llm_service = None
        self.cache_dir = Path('data/hot_cache')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_llm_cache_key(self, topics: List[Dict], count: int, platform: str) -> str:
        """生成LLM缓存键"""
        topics_hash = hashlib.md5(
            json.dumps(topics, sort_keys=True).encode('utf-8')
        ).hexdigest()
        return f"llm_analysis_{platform}_{count}_{topics_hash}"
    
    def _get_llm_cache(self, cache_key: str) -> Optional[List[Dict]]:
        """获取LLM缓存"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"使用LLM缓存: {cache_key}")
                    return data.get('topics', [])
            except Exception as e:
                logger.warning(f"读取LLM缓存失败: {e}")
        return None
    
    def _save_llm_cache(self, cache_key: str, topics: List[Dict]):
        """保存LLM缓存"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({'topics': topics, 'timestamp': datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)
            logger.info(f"保存LLM缓存: {cache_key}")
        except Exception as e:
            logger.warning(f"保存LLM缓存失败: {e}")
    
    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            config_path = "app/skills/skills/collection/topic_discovery/assets/hot_sources.yaml"
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"加载配置文件失败，使用默认配置: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            'sources': ['weibo', 'baidu', 'toutiao'],
            'discovery': {
                'cache_ttl': 3600,
                'topic_count': 5,
                'min_heat': 0,
                'exclude_keywords': ['广告', '推广', '营销']
            }
        }
    
    def set_llm_service(self, llm_service):
        """设置LLM服务"""
        self.llm_service = llm_service
    
    async def execute(self, config: Dict) -> Dict:
        """
        执行主题发现
        
        Args:
            config: 配置参数
                - sources: 数据源列表 ['weibo', 'baidu', 'toutiao']
                - platform: 目标平台
                - category: 内容分类
                - count: 推荐主题数量
                - use_llm: 是否使用LLM分析（默认True）
        
        Returns:
            {
                'topics': [
                    {
                        'topic': '主题标题',
                        'score': 0.95,
                        'reason': '推荐理由',
                        'keywords': ['关键词1', '关键词2'],
                        'source': '数据源',
                        'details': '详细内容'
                    }
                ],
                'total_found': 总数
            }
        """
        sources = config.get('sources', ['weibo', 'baidu', 'toutiao'])
        count = config.get('count', 5)
        use_llm = config.get('use_llm', True)
        force_refresh = config.get('force_refresh', False)
        platform = config.get('platform', 'xiaohongshu')
        
        logger.info(f"开始主题发现: sources={sources}, count={count}, use_llm={use_llm}, platform={platform}")
        
        all_topics = []
        
        hot_data = await self.hot_fetcher.fetch_all(sources, force=force_refresh)
        
        for source, items in hot_data.items():
            logger.info(f"从 {source} 获取到 {len(items)} 条热点")
            
            for item in items:
                topic = {
                    'topic': item.get('title', ''),
                    'rank': item.get('rank', ''),
                    'heat': item.get('heat', ''),
                    'tag': item.get('tag', ''),
                    'url': item.get('url', ''),
                    'desc': item.get('desc', ''),
                    'source': source,
                    'source_name': item.get('source_name', source),
                    'is_top': item.get('is_top', False),
                    'score': self._calculate_score(item),
                    'reason': f"来自{item.get('source_name', source)}的热点内容"
                }
                all_topics.append(topic)
        
        filtered_topics = self._filter_topics(all_topics, config)
        
        if use_llm and self.llm_service:
            logger.info("使用LLM分析选择最热门主题...")
            final_topics = await self._analyze_with_llm(filtered_topics, count, platform)
        else:
            sorted_topics = self._rank_topics(filtered_topics)
            final_topics = sorted_topics[:count]
        
        logger.info(f"最终推荐 {len(final_topics)} 个主题")
        
        return {
            'topics': final_topics,
            'total_found': len(all_topics)
        }
    
    def _calculate_score(self, item: Dict) -> float:
        """
        计算主题分数
        
        Args:
            item: 热点数据项
        
        Returns:
            分数（0-1）
        """
        score = 0.5
        
        rank = item.get('rank', '')
        if rank and rank.isdigit():
            rank_num = int(rank)
            if rank_num <= 10:
                score += 0.3
            elif rank_num <= 20:
                score += 0.2
            elif rank_num <= 50:
                score += 0.1
        
        if item.get('is_top'):
            score += 0.1
        
        tag = item.get('tag', '')
        if tag in ['热', '沸', '新']:
            score += 0.1
        
        return min(score, 1.0)
    
    def _filter_topics(self, topics: List[Dict], config: Dict) -> List[Dict]:
        """过滤主题"""
        exclude_keywords = self.config.get('discovery', {}).get('exclude_keywords', [])
        
        filtered = []
        for topic in topics:
            title = topic.get('topic', '')
            
            if not title or len(title) < 2:
                continue
            
            should_exclude = False
            for keyword in exclude_keywords:
                if keyword in title:
                    should_exclude = True
                    break
            
            if not should_exclude:
                filtered.append(topic)
        
        return filtered
    
    def _rank_topics(self, topics: List[Dict]) -> List[Dict]:
        """排序主题"""
        sorted_topics = sorted(topics, key=lambda x: x.get('score', 0), reverse=True)
        return sorted_topics
    
    async def _analyze_with_llm(self, topics: List[Dict], count: int, platform: str = 'xiaohongshu') -> List[Dict]:
        """
        使用LLM分析选择最热门的主题
        
        Args:
            topics: 候选主题列表
            count: 需要选择的数量
            platform: 目标平台（xiaohongshu, weixin, douyin等）
        
        Returns:
            LLM选择的主题列表
        """
        if not self.llm_service:
            logger.warning("LLM服务未设置，使用默认排序")
            return self._rank_topics(topics)[:count]
        
        try:
            # 检查缓存
            cache_key = self._get_llm_cache_key(topics, count, platform)
            cached_topics = self._get_llm_cache(cache_key)
            
            if cached_topics:
                logger.info(f"使用LLM缓存结果: {len(cached_topics)} 个主题")
                return cached_topics
            
            logger.info("LLM缓存未命中，开始分析...")
            
            topics_text = ""
            for i, topic in enumerate(topics[:50], 1):
                topics_text += f"{i}. {topic['topic']}"
                if topic.get('heat'):
                    topics_text += f" (热度: {topic['heat']})"
                if topic.get('tag'):
                    topics_text += f" [{topic['tag']}]"
                topics_text += f" - 来源: {topic['source_name']}\n"
            
            platform_desc = {
                'xiaohongshu': '小红书用户主要是年轻女性，关注美妆、穿搭、生活方式、职场成长、情感话题',
                'weixin': '微信公众号用户年龄层较广，关注深度内容、职场技能、生活感悟、社会热点',
                'douyin': '抖音用户喜欢娱乐、搞笑、生活技巧、情感故事、热点话题'
            }
            
            platform_info = platform_desc.get(platform, '综合平台用户')
            
            prompt = f"""你是一位专业的内容策划专家，请从以下热点话题中选择{count}个最适合{platform}平台的主题。

目标平台：{platform}
平台用户特征：{platform_info}

热点话题列表：
{topics_text}

请按以下JSON格式返回结果：
{{
  "selected_topics": [
    {{
      "index": 话题序号,
      "topic": "话题标题",
      "reason": "为什么这个话题适合{platform}平台的用户（具体分析用户兴趣点）",
      "content_direction": "针对{platform}平台的内容创作方向（具体到标题风格、内容结构、呈现方式）",
      "keywords": ["关键词1", "关键词2", "关键词3"],
      "target_audience": "具体的目标受众画像（年龄、性别、职业、兴趣）",
      "predicted_heat": "预测热度（高/中/低）",
      "engagement_potential": "互动潜力分析（评论、点赞、转发可能性）"
    }}
  ]
}}

选择标准：
1. 符合{platform}平台用户的兴趣偏好
2. 具有高传播潜力和互动性
3. 内容创作空间大，容易引发共鸣
4. 结合当前热点趋势，有时效性
5. 避免敏感话题和负面内容

请只返回JSON，不要包含其他内容。"""

            result = await self.llm_service.generate_text(
                prompt,
                provider='deepseek',
                max_tokens=2000
            )
            
            if 'error' in result:
                logger.error(f"LLM生成失败: {result['error']}")
                return self._rank_topics(topics)[:count]
            
            response = result.get('generated_text', '')
            
            import re
            
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                selected = result.get('selected_topics', [])
                
                final_topics = []
                for item in selected:
                    index = item.get('index', 1) - 1
                    if 0 <= index < len(topics):
                        topic = topics[index].copy()
                        topic['reason'] = item.get('reason', '')
                        topic['content_direction'] = item.get('content_direction', '')
                        topic['keywords'] = item.get('keywords', [])
                        topic['target_audience'] = item.get('target_audience', '')
                        topic['predicted_heat'] = item.get('predicted_heat', '')
                        topic['details'] = item.get('content_direction', '')
                        final_topics.append(topic)
                
                logger.info(f"LLM选择了 {len(final_topics)} 个主题")
                
                # 保存缓存
                self._save_llm_cache(cache_key, final_topics)
                
                return final_topics
            
        except Exception as e:
            logger.error(f"LLM分析失败: {e}")
        
        return self._rank_topics(topics)[:count]


async def main():
    """测试函数"""
    skill = TopicDiscoverySkill()
    
    llm_service = create_llm_service_from_env()
    skill.set_llm_service(llm_service)
    
    config = {
        'sources': ['weibo', 'baidu', 'toutiao'],
        'count': 3,
        'use_llm': True
    }
    
    result = await skill.execute(config)
    
    print("\n" + "="*80)
    print("🎯 主题发现结果")
    print("="*80)
    
    for i, topic in enumerate(result['topics'], 1):
        print(f"\n{i}. {topic['topic']}")
        print(f"   来源: {topic['source_name']}")
        print(f"   排名: {topic.get('rank', '')}")
        print(f"   热度: {topic.get('heat', '')}")
        print(f"   推荐理由: {topic.get('reason', '')}")
        if topic.get('content_direction'):
            print(f"   内容方向: {topic.get('content_direction')}")
        if topic.get('keywords'):
            print(f"   关键词: {', '.join(topic['keywords'])}")
    
    print(f"\n总计发现: {result['total_found']} 个主题")
    print(f"推荐数量: {len(result['topics'])} 个")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
