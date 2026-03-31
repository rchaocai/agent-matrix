"""
统计数据API路由
"""

from fastapi import APIRouter
from typing import List, Dict, Any
from app.models import Agent, Draft
from tortoise import functions
from datetime import datetime, timedelta

router = APIRouter()


@router.get("/overview")
async def get_statistics_overview() -> Dict[str, Any]:
    """获取统计数据概览"""
    # 总发文数
    total_posts = await Draft.filter(status="published").count()

    # 今日发文数
    from datetime import timezone
    now_utc = datetime.now(timezone.utc)
    today_utc = now_utc.date()
    today_start = datetime.combine(today_utc, datetime.min.time())
    
    today_published = await Draft.filter(
        created_at__gte=today_start,
        status="published"
    ).count()

    # 总粉丝数（TODO: 从Account聚合）
    total_followers = 0

    # 总互动量（TODO: 从平台数据获取）
    total_likes = 0

    # 平均质量分（TODO: 从Review表计算）
    avg_quality_score = 85.6

    # 增长率（模拟数据）
    posts_growth = 12.5
    followers_growth = 8.3
    likes_growth = 15.7
    quality_trend = 2.3

    return {
        "totalPosts": total_posts,
        "todayPublished": today_published,
        "totalFollowers": total_followers,
        "totalLikes": total_likes,
        "avgQualityScore": avg_quality_score,
        "postsGrowth": posts_growth,
        "followersGrowth": followers_growth,
        "likesGrowth": likes_growth,
        "qualityTrend": quality_trend
    }


@router.get("/agents")
async def get_agent_statistics(limit: int = 10) -> List[Dict[str, Any]]:
    """获取Agent详细统计数据"""
    agents_data = await Agent.all().limit(limit)

    result = []
    for agent in agents_data:
        # 统计该Agent的发文数
        posts_count = await Draft.filter(
            agent_id=agent.id,
            status="published"
        ).count()

        # 估算互动数（发文数 * 100）
        interactions = posts_count * 100

        result.append({
            "id": agent.id,
            "name": agent.name,
            "avatar": "📝",  # TODO: 从config获取
            "platform": "xiaohongshu",  # TODO: 从config解析
            "posts": posts_count,
            "followers": 0,  # TODO: 从实际数据获取
            "likes": interactions,  # TODO: 从平台数据获取
            "comments": int(interactions * 0.2),
            "qualityScore": 85,  # TODO: 从Review平均分计算
            "approvalRate": 90,  # TODO: 从Review表计算
            "engagementRate": 10.5  # TODO: 计算实际互动率
        })

    return result


@router.get("/trend")
async def get_post_trend(days: int = 30) -> Dict[str, Any]:
    """获取发文趋势数据（最近N天）"""
    from datetime import timezone
    trend_data = []
    labels = []

    for i in range(days):
        date = datetime.now(timezone.utc).date() - timedelta(days=days-1-i)
        
        # 将 date 转换为 datetime
        date_start = datetime.combine(date, datetime.min.time())
        date_end = datetime.combine(date + timedelta(days=1), datetime.min.time())

        # 统计该日期的发文数
        count = await Draft.filter(
            created_at__gte=date_start,
            created_at__lt=date_end,
            status="published"
        ).count()

        trend_data.append(count)
        labels.append(date.strftime("%m-%d"))

    return {
        "labels": labels,
        "data": trend_data,
        "total": sum(trend_data)
    }


@router.get("/top-content")
async def get_top_content(limit: int = 10) -> List[Dict[str, Any]]:
    """获取热门内容排行"""
    # TODO: 应该根据互动量排序
    drafts = await Draft.filter(
        status="published"
    ).order_by("-created_at").limit(limit)

    result = []
    for draft in drafts:
        # 获取Agent信息
        agent = await Agent.get_or_none(id=draft.agent_id)

        result.append({
            "id": draft.id,
            "title": draft.title,
            "agentName": agent.name if agent else draft.agent_id,
            "avatar": "📝",
            "likes": 0,  # TODO: 从平台获取
            "comments": 0,  # TODO: 从平台获取
            "platform": draft.platform
        })

    return result
