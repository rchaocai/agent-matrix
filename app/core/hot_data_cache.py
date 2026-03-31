"""
热点数据缓存管理器
实现每天只爬一次的缓存机制
"""
import json
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class HotDataCache:
    """热点数据缓存管理器"""
    
    def __init__(self, cache_dir: str = "data/hot_cache"):
        """
        初始化缓存管理器
        
        Args:
            cache_dir: 缓存目录
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_file(self, source: str) -> Path:
        """
        获取缓存文件路径
        
        Args:
            source: 数据源名称（weibo, baidu, toutiao等）
        
        Returns:
            缓存文件路径
        """
        today = date.today().strftime("%Y%m%d")
        return self.cache_dir / f"{source}_{today}.json"
    
    def _get_metadata_file(self) -> Path:
        """获取元数据文件路径"""
        return self.cache_dir / "metadata.json"
    
    def load_metadata(self) -> Dict:
        """加载元数据"""
        metadata_file = self._get_metadata_file()
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载元数据失败: {e}")
        
        return {
            'last_update': {},
            'sources': {}
        }
    
    def save_metadata(self, metadata: Dict):
        """保存元数据"""
        metadata_file = self._get_metadata_file()
        try:
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存元数据失败: {e}")
    
    def is_cache_valid(self, source: str) -> bool:
        """
        检查缓存是否有效（今天是否已爬取）
        
        Args:
            source: 数据源名称
        
        Returns:
            缓存是否有效
        """
        cache_file = self._get_cache_file(source)
        
        if not cache_file.exists():
            return False
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not data or 'timestamp' not in data:
                return False
            
            cache_date = datetime.fromisoformat(data['timestamp']).date()
            today = date.today()
            
            return cache_date == today
        
        except Exception as e:
            logger.warning(f"检查缓存有效性失败: {e}")
            return False
    
    def get_cached_data(self, source: str) -> Optional[List[Dict]]:
        """
        获取缓存数据
        
        Args:
            source: 数据源名称
        
        Returns:
            缓存的热点数据列表，如果缓存无效则返回None
        """
        if not self.is_cache_valid(source):
            return None
        
        cache_file = self._get_cache_file(source)
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"从缓存加载 {source} 数据: {len(data.get('items', []))} 条")
            return data.get('items', [])
        
        except Exception as e:
            logger.error(f"加载缓存数据失败: {e}")
            return None
    
    def save_cache(self, source: str, items: List[Dict]) -> bool:
        """
        保存数据到缓存
        
        Args:
            source: 数据源名称
            items: 热点数据列表
        
        Returns:
            是否保存成功
        """
        cache_file = self._get_cache_file(source)
        
        try:
            data = {
                'source': source,
                'timestamp': datetime.now().isoformat(),
                'date': date.today().isoformat(),
                'total': len(items),
                'items': items
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"已保存 {source} 数据到缓存: {len(items)} 条")
            
            metadata = self.load_metadata()
            metadata['last_update'][source] = datetime.now().isoformat()
            metadata['sources'][source] = {
                'total': len(items),
                'date': date.today().isoformat()
            }
            self.save_metadata(metadata)
            
            return True
        
        except Exception as e:
            logger.error(f"保存缓存失败: {e}")
            return False
    
    def get_all_cached_data(self, sources: List[str] = None) -> Dict[str, List[Dict]]:
        """
        获取所有数据源的缓存数据
        
        Args:
            sources: 数据源列表，如果为None则获取所有
        
        Returns:
            数据源名称到数据列表的映射
        """
        if sources is None:
            sources = ['weibo', 'baidu', 'toutiao']
        
        all_data = {}
        
        for source in sources:
            data = self.get_cached_data(source)
            if data:
                all_data[source] = data
        
        return all_data
    
    def clear_old_cache(self, days: int = 7):
        """
        清理旧缓存

        Args:
            days: 保留最近几天的缓存
        """
        import time

        cutoff_time = time.time() - (days * 24 * 60 * 60)

        for cache_file in self.cache_dir.glob("*.json"):
            if cache_file.name == "metadata.json":
                continue

            try:
                if cache_file.stat().st_mtime < cutoff_time:
                    cache_file.unlink()
                    logger.info(f"已删除旧缓存: {cache_file.name}")
            except Exception as e:
                logger.warning(f"删除缓存文件失败: {e}")

    def get_cache_file_by_date(self, source: str, date_str: str) -> Path:
        """
        获取指定日期的缓存文件路径

        Args:
            source: 数据源名称（weibo, baidu, toutiao等）
            date_str: 日期字符串（YYYY-MM-DD格式）

        Returns:
            缓存文件路径
        """
        try:
            # 将 YYYY-MM-DD 转换为 YYYYMMDD
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            date_filename = date_obj.strftime("%Y%m%d")
            return self.cache_dir / f"{source}_{date_filename}.json"
        except ValueError:
            logger.error(f"无效的日期格式: {date_str}")
            return None

    def get_cached_data_by_date(self, source: str, date_str: str) -> Optional[Dict[str, Any]]:
        """
        获取指定日期的缓存数据

        Args:
            source: 数据源名称
            date_str: 日期字符串（YYYY-MM-DD格式）

        Returns:
            缓存的热点数据对象，包含source、timestamp、date、total、items字段
            如果缓存不存在则返回None
        """
        cache_file = self.get_cache_file_by_date(source, date_str)

        if not cache_file or not cache_file.exists():
            return None

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            logger.info(f"从缓存加载 {source} {date_str} 的数据: {len(data.get('items', []))} 条")
            return data

        except Exception as e:
            logger.error(f"加载缓存数据失败 ({source} {date_str}): {e}")
            return None

    def get_available_dates(self) -> List[str]:
        """
        扫描缓存目录，获取所有可用日期列表

        Returns:
            日期列表（YYYY-MM-DD格式），按降序排列（最新在前）
        """
        dates = set()

        for cache_file in self.cache_dir.glob("*.json"):
            if cache_file.name == "metadata.json":
                continue

            # 从文件名提取日期: weibo_20260315.json
            parts = cache_file.stem.split('_')
            if len(parts) >= 2:
                date_str = parts[-1]
                try:
                    # 将 YYYYMMDD 转换为 YYYY-MM-DD
                    dt = datetime.strptime(date_str, "%Y%m%d")
                    formatted_date = dt.strftime("%Y-%m-%d")
                    dates.add(formatted_date)
                except ValueError:
                    logger.warning(f"跳过无效的缓存文件名: {cache_file.name}")

        # 按降序排列（最新在前）
        return sorted(list(dates), reverse=True)
