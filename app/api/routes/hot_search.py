"""
热搜数据API路由
提供热搜数据查询、手动爬取等功能
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import date, datetime
from app.core.hot_data_fetcher import HotDataFetcher
from app.core.hot_data_cache import HotDataCache
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# 初始化fetcher和cache
hot_fetcher = HotDataFetcher()
hot_cache = HotDataCache()


@router.get("/data")
async def get_hot_search_data(
    date: Optional[str] = Query(None, description="日期 YYYY-MM-DD，默认今天"),
    sources: Optional[List[str]] = Query(None, description="数据源列表，默认全部")
) -> Dict[str, Any]:
    """
    获取指定日期的热搜数据

    Args:
        date: 日期字符串（YYYY-MM-DD），不传则默认今天
        sources: 数据源列表，不传则默认查询全部（weibo, baidu, toutiao）

    Returns:
        包含各平台热搜数据的字典
    """
    try:
        # 处理日期参数
        from datetime import date as date_class
        target_date = date if date else date_class.today().isoformat()

        # 处理数据源参数
        if sources is None:
            sources = ['weibo', 'baidu', 'toutiao']

        # 构建返回结果
        result = {
            "date": target_date,
            "sources": {}
        }

        # 获取各平台数据
        for source in sources:
            try:
                # 如果是今天，使用原有的get_cached_data方法（检查缓存有效性）
                if target_date == date_class.today().isoformat():
                    items = hot_cache.get_cached_data(source)

                    # 如果今天没有缓存，尝试爬取
                    if items is None:
                        logger.info(f"今天 {source} 暂无缓存，尝试爬取...")
                        if source == 'weibo':
                            items = await hot_fetcher.fetch_weibo(force=False)
                        elif source == 'baidu':
                            items = await hot_fetcher.fetch_baidu(force=False)
                        elif source == 'toutiao':
                            items = await hot_fetcher.fetch_toutiao(force=False)
                        else:
                            items = []

                    # 获取元数据
                    metadata = hot_cache.load_metadata()
                    timestamp = metadata.get('last_update', {}).get(source)
                    total = len(items) if items else 0

                    result["sources"][source] = {
                        "total": total,
                        "items": items or [],
                        "cached": items is not None,
                        "timestamp": timestamp
                    }
                else:
                    # 历史日期，使用get_cached_data_by_date方法
                    data = hot_cache.get_cached_data_by_date(source, target_date)

                    if data:
                        result["sources"][source] = {
                            "total": data.get('total', 0),
                            "items": data.get('items', []),
                            "cached": True,
                            "timestamp": data.get('timestamp')
                        }
                    else:
                        result["sources"][source] = {
                            "total": 0,
                            "items": [],
                            "cached": False,
                            "timestamp": None
                        }

            except Exception as e:
                logger.error(f"获取 {source} 数据失败: {e}")
                result["sources"][source] = {
                    "total": 0,
                    "items": [],
                    "cached": False,
                    "timestamp": None,
                    "error": str(e)
                }

        return result

    except Exception as e:
        logger.error(f"获取热搜数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取热搜数据失败: {str(e)}")


@router.post("/fetch")
async def fetch_hot_search(
    sources: Optional[List[str]] = None,
    force: bool = False
) -> Dict[str, Any]:
    """
    手动触发爬取热搜数据

    Args:
        sources: 要爬取的数据源列表，不传则默认全部
        force: 是否强制重新爬取（忽略缓存）

    Returns:
        爬取结果
    """
    try:
        # 处理数据源参数
        if sources is None:
            sources = ['weibo', 'baidu', 'toutiao']

        logger.info(f"开始手动爬取热搜数据，sources={sources}, force={force}")

        # 使用HotDataFetcher进行爬取
        results = await hot_fetcher.fetch_all(sources=sources, force=force)

        # 构建返回结果
        response = {
            "success": True,
            "message": "爬取成功",
            "results": {},
            "timestamp": datetime.now().isoformat()
        }

        for source, items in results.items():
            response["results"][source] = {
                "success": items is not None,
                "count": len(items) if items else 0
            }

        logger.info(f"爬取完成: {response}")
        return response

    except Exception as e:
        logger.error(f"爬取热搜数据失败: {e}")
        return {
            "success": False,
            "message": f"爬取失败: {str(e)}",
            "results": {},
            "timestamp": datetime.now().isoformat()
        }


@router.get("/dates")
async def get_available_dates() -> Dict[str, List[str]]:
    """
    获取所有可用日期列表

    Returns:
        日期列表（YYYY-MM-DD格式），按降序排列（最新在前）
    """
    try:
        dates = hot_cache.get_available_dates()
        return {
            "dates": dates
        }
    except Exception as e:
        logger.error(f"获取可用日期列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取可用日期列表失败: {str(e)}")


@router.get("/status")
async def get_cache_status() -> Dict[str, Any]:
    """
    获取当前缓存状态

    Returns:
        包含各平台缓存状态的字典
    """
    try:
        # 获取元数据
        metadata = hot_cache.load_metadata()

        # 构建返回结果
        result = {
            "sources": {},
            "metadata": metadata
        }

        # 检查各平台缓存状态
        for source in ['weibo', 'baidu', 'toutiao']:
            is_valid = hot_cache.is_cache_valid(source)

            if is_valid:
                # 获取缓存数据
                items = hot_cache.get_cached_data(source)
                source_metadata = metadata.get('sources', {}).get(source, {})

                result["sources"][source] = {
                    "cached": True,
                    "timestamp": metadata.get('last_update', {}).get(source),
                    "total": len(items) if items else 0,
                    "date": source_metadata.get('date')
                }
            else:
                result["sources"][source] = {
                    "cached": False,
                    "timestamp": None,
                    "total": 0,
                    "date": None
                }

        return result

    except Exception as e:
        logger.error(f"获取缓存状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取缓存状态失败: {str(e)}")
