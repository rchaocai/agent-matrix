"""
热点数据获取器 - 统一接口
整合微博、百度、头条等数据源
"""
import asyncio
import logging
from typing import List, Dict, Optional
from pathlib import Path
import sys
import importlib.util

sys.path.insert(0, str(Path(__file__).parent.parent))


def load_module_from_file(module_name, file_path):
    """从文件路径加载模块"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


hot_data_cache = load_module_from_file(
    "hot_data_cache",
    str(Path(__file__).parent / "hot_data_cache.py")
)
HotDataCache = hot_data_cache.HotDataCache

WeiboHotSearch = load_module_from_file(
    "WeiboHotFetcher",
    str(Path(__file__).parent.parent / "function" / "WeiboHotFetcher.py")
).WeiboHotSearch

BaiduHotSearchFetcher = load_module_from_file(
    "BaiduHotSearchFetcher",
    str(Path(__file__).parent.parent / "function" / "BaiduHotSearchFetcher.py")
).BaiduHotSearchFetcher

ToutiaoHotSearch = load_module_from_file(
    "ToutiaoPageFetcher",
    str(Path(__file__).parent.parent / "function" / "ToutiaoPageFetcher.py")
).ToutiaoHotSearch

logger = logging.getLogger(__name__)


class HotDataFetcher:
    """热点数据获取器 - 统一接口"""
    
    def __init__(self, cache_dir: str = "data/hot_cache"):
        """
        初始化
        
        Args:
            cache_dir: 缓存目录
        """
        self.cache = HotDataCache(cache_dir)
    
    async def fetch_weibo(self, force: bool = False) -> List[Dict]:
        """
        获取微博热搜
        
        Args:
            force: 是否强制重新获取（忽略缓存）
        
        Returns:
            热搜数据列表
        """
        source = 'weibo'
        
        if not force and self.cache.is_cache_valid(source):
            return self.cache.get_cached_data(source)
        
        logger.info("开始获取微博热搜...")
        
        try:
            fetcher = WeiboHotSearch(headless=True)
            items = await fetcher.fetch_hot_search()
            
            normalized_items = []
            for item in items:
                normalized_items.append({
                    'title': item.get('title', ''),
                    'rank': item.get('rank', ''),
                    'heat': item.get('heat', ''),
                    'tag': item.get('tag', ''),
                    'url': item.get('link', ''),
                    'is_top': item.get('is_top', False),
                    'source': 'weibo',
                    'source_name': '微博热搜'
                })
            
            self.cache.save_cache(source, normalized_items)
            
            return normalized_items
        
        except Exception as e:
            logger.error(f"获取微博热搜失败: {e}")
            cached = self.cache.get_cached_data(source)
            return cached if cached else []
    
    async def fetch_baidu(self, force: bool = False) -> List[Dict]:
        """
        获取百度热搜
        
        Args:
            force: 是否强制重新获取（忽略缓存）
        
        Returns:
            热搜数据列表
        """
        source = 'baidu'
        
        if not force and self.cache.is_cache_valid(source):
            return self.cache.get_cached_data(source)
        
        logger.info("开始获取百度热搜...")
        
        try:
            fetcher = BaiduHotSearchFetcher(headless=True)
            items = await fetcher.get_hot_search()
            
            normalized_items = []
            for item in items:
                normalized_items.append({
                    'title': item.get('word', ''),
                    'rank': item.get('rank', ''),
                    'heat': item.get('hot_score', ''),
                    'tag': item.get('hot_tag', ''),
                    'url': item.get('url', ''),
                    'desc': item.get('desc', ''),
                    'is_top': item.get('is_top', False),
                    'source': 'baidu',
                    'source_name': '百度热搜'
                })
            
            self.cache.save_cache(source, normalized_items)
            
            return normalized_items
        
        except Exception as e:
            logger.error(f"获取百度热搜失败: {e}")
            cached = self.cache.get_cached_data(source)
            return cached if cached else []
    
    async def fetch_toutiao(self, force: bool = False) -> List[Dict]:
        """
        获取今日头条热搜
        
        Args:
            force: 是否强制重新获取（忽略缓存）
        
        Returns:
            热搜数据列表
        """
        source = 'toutiao'
        
        if not force and self.cache.is_cache_valid(source):
            return self.cache.get_cached_data(source)
        
        logger.info("开始获取今日头条热搜...")
        
        try:
            fetcher = ToutiaoHotSearch(headless=True)
            items = await fetcher.fetch_all_hot_search(refresh_times=2)
            
            normalized_items = []
            for item in items:
                normalized_items.append({
                    'title': item.get('title', ''),
                    'rank': item.get('rank', ''),
                    'tag': item.get('tag', ''),
                    'url': item.get('link', ''),
                    'is_top': item.get('is_top', False),
                    'source': 'toutiao',
                    'source_name': '今日头条'
                })
            
            self.cache.save_cache(source, normalized_items)
            
            return normalized_items
        
        except Exception as e:
            logger.error(f"获取今日头条热搜失败: {e}")
            cached = self.cache.get_cached_data(source)
            return cached if cached else []
    
    async def fetch_all(self, sources: List[str] = None, force: bool = False) -> Dict[str, List[Dict]]:
        """
        获取所有数据源的热点数据
        
        Args:
            sources: 数据源列表，如果为None则获取所有
            force: 是否强制重新获取（忽略缓存）
        
        Returns:
            数据源名称到数据列表的映射
        """
        if sources is None:
            sources = ['weibo', 'baidu', 'toutiao']
        
        tasks = []
        source_map = {
            'weibo': self.fetch_weibo,
            'baidu': self.fetch_baidu,
            'toutiao': self.fetch_toutiao
        }
        
        for source in sources:
            if source in source_map:
                tasks.append((source, source_map[source](force)))
        
        results = {}
        
        for source, task in tasks:
            try:
                data = await task
                results[source] = data
                logger.info(f"获取 {source} 数据成功: {len(data)} 条")
            except Exception as e:
                logger.error(f"获取 {source} 数据失败: {e}")
                results[source] = []
        
        return results
    
    def get_all_cached(self, sources: List[str] = None) -> Dict[str, List[Dict]]:
        """
        获取所有缓存数据（不重新爬取）
        
        Args:
            sources: 数据源列表，如果为None则获取所有
        
        Returns:
            数据源名称到数据列表的映射
        """
        return self.cache.get_all_cached_data(sources)


async def main():
    """测试函数"""
    logging.basicConfig(level=logging.INFO)
    
    fetcher = HotDataFetcher()
    
    print("\n" + "="*80)
    print("开始获取热点数据...")
    print("="*80)
    
    results = await fetcher.fetch_all(force=False)
    
    for source, items in results.items():
        print(f"\n{source}: {len(items)} 条")
        if items:
            print(f"  前3条:")
            for item in items[:3]:
                print(f"    {item.get('rank', '')}. {item.get('title', '')} - {item.get('heat', '')}")


if __name__ == "__main__":
    asyncio.run(main())
