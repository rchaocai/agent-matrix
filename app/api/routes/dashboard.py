"""
仪表盘统计API路由
"""

from fastapi import APIRouter, Query
from typing import Dict, Any
from app.models import Agent, Content, Task, Draft, Review, Account
from tortoise.functions import Count
from datetime import datetime, timedelta, timezone, date
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats() -> Dict[str, Any]:
    """获取仪表盘核心统计数据"""
    try:
        # Agent统计
        total_agents = await Agent.all().count()
        active_agents = await Agent.filter(enabled=True).count()

        # Draft统计
        # 使用北京时间计算今日
        now_local = datetime.now()
        today_local = now_local.date()
        today_start_local = datetime.combine(today_local, datetime.min.time())
        # 将北京时间转换为 UTC 时间（减8小时）用于查询
        today_start_utc = today_start_local - timedelta(hours=8)
        
        logger.info(f"时间调试: now_local={now_local}, today_local={today_local}, today_start_utc={today_start_utc}")
        
        # 查询今日已发文（使用 created_at）
        today_published = await Draft.filter(
            created_at__gte=today_start_utc,
            status="published"
        ).count()
        
        logger.info(f"今日发文查询结果: today_start_utc={today_start_utc}, count={today_published}")

        total_drafts = await Draft.all().count()
        published_drafts = await Draft.filter(status="published").count()
        # 草稿箱待发布（未发布的草稿）
        unpublished_drafts = await Draft.filter(status="pending").count()

        # 待审核内容（从 reviews 表统计 pending 状态的审核记录）
        pending_review = await Review.filter(status="pending").count()

        # Account统计
        total_accounts = await Account.all().count()
        active_accounts = await Account.filter(enabled=True).count()

        # 审批率
        approval_rate = 0
        if published_drafts > 0:
            approved_reviews = await Review.filter(status="approved").count()
            approval_rate = round((approved_reviews / published_drafts) * 100)

        # 获取最新时间
        last_review = await Review.filter().order_by("-created_at").first()
        last_review_time = format_time_ago(last_review.created_at) if last_review else "无"

        last_task = await Task.filter().order_by("-started_at").first()
        last_run_time = format_time_ago(last_task.started_at) if last_task else "无"

        # 获取下次运行时间
        next_run_time = None
        try:
            from app.main import scheduler_service
            if not scheduler_service:
                next_run_time = "调度器未启动"
            else:
                # 获取所有已调度的任务
                jobs = scheduler_service.get_scheduled_jobs()

                if jobs:
                    # 找出最近的一次运行时间
                    # 使用带时区的当前时间（与scheduler的时区一致）
                    now = datetime.now(timezone.utc)
                    upcoming_runs = []
                    for job in jobs:
                        if job.get('next_run_time'):
                            try:
                                run_time = datetime.fromisoformat(job['next_run_time'])
                                # 转换为UTC进行比较
                                if run_time.tzinfo:
                                    run_time_utc = run_time.astimezone(timezone.utc)
                                else:
                                    run_time_utc = run_time.replace(tzinfo=timezone.utc)
                                upcoming_runs.append(run_time_utc)
                            except Exception as e:
                                logger.error(f"解析时间失败 {job['id']}: {e}")

                    if upcoming_runs:
                        next_run = min(upcoming_runs)
                        # 转换为本地时区显示
                        local_time = next_run.astimezone(timezone(timedelta(hours=8)))
                        # 格式化为友好的时间显示
                        if local_time.date() == now.date():
                            next_run_time = local_time.strftime("%H:%M")
                        else:
                            next_run_time = local_time.strftime("%m-%d %H:%M")
                    else:
                        next_run_time = "无即将运行的任务"
                else:
                    next_run_time = "无调度任务"
        except Exception as e:
            logger.error(f"获取下次运行时间失败: {str(e)}", exc_info=True)
            next_run_time = None

        return {
            "totalAgents": total_agents,
            "activeAgents": active_agents,
            "todayPublished": today_published,
            "pendingReview": pending_review,
            "totalDrafts": unpublished_drafts,
            "activeAccounts": active_accounts,
            "totalAccounts": total_accounts,
            "approvalRate": approval_rate,
            "lastReviewTime": last_review_time,
            "lastRunTime": last_run_time,
            "nextRunTime": next_run_time
        }
    except Exception as e:
        logger.error(f"获取仪表盘统计失败: {str(e)}", exc_info=True)
        # 返回默认值
        return {
            "totalAgents": 0,
            "activeAgents": 0,
            "todayPublished": 0,
            "pendingReview": 0,
            "totalDrafts": 0,
            "activeAccounts": 0,
            "totalAccounts": 0,
            "approvalRate": 0,
            "lastReviewTime": "无",
            "lastRunTime": "无",
            "nextRunTime": None
        }


@router.get("/recent-posts")
async def get_recent_posts(limit: int = Query(default=10, le=50)) -> list:
    """获取最近发文列表"""
    try:
        drafts = await Draft.filter(
            status="published"
        ).order_by("-created_at").limit(limit)

        results = []
        for draft in drafts:
            # 获取对应的Agent信息
            agent = await Agent.get_or_none(id=draft.agent_id)

            results.append({
                "id": draft.id,
                "avatar": "📝",
                "agentName": agent.name if agent else draft.agent_id,
                "time": format_time(draft.created_at),
                "summary": draft.title or (draft.content[:100] + "..." if draft.content and len(draft.content) > 100 else draft.content or ""),
                "likes": 0,  # TODO: 从平台获取
                "comments": 0,  # TODO: 从平台获取
                "status": "published",
                "statusText": "已发",
                "statusClass": "success"
            })

        return results
    except Exception as e:
        logger.error(f"获取最近发文失败: {str(e)}", exc_info=True)
        return []


@router.get("/trend")
async def get_post_trend(days: int = Query(default=7, le=30)) -> Dict[str, Any]:
    """获取发文趋势数据（最近N天）"""
    trend_data = []
    labels = []

    for i in range(days):
        date = datetime.now().date() - timedelta(days=days-1-i)
        date_str = date.strftime("%Y-%m-%d")

        # 统计该日期的发文数
        count = await Draft.filter(
            created_at__gte=date,
            created_at__lt=date + timedelta(days=1),
            status="published"
        ).count()

        trend_data.append(count)
        labels.append(["周一", "周二", "周三", "周四", "周五", "周六", "周日"][date.weekday()])

    return {
        "labels": labels,
        "data": trend_data
    }


@router.get("/top-agents")
async def get_top_agents(limit: int = Query(default=5, le=20)) -> list:
    """获取热门Agent排行（使用聚合查询避免N+1）"""
    try:
        # 使用聚合查询统计每个Agent的发文数
        from tortoise import connections
        from typing import NamedTuple

        # 直接使用SQL查询避免N+1问题
        conn = connections.get("default")

        # 执行聚合查询
        results = await conn.execute_query_dict(
            f"""
            SELECT
                a.id,
                a.name,
                a.enabled,
                COUNT(d.id) as draft_count,
                MAX(a.updated_at) as last_run
            FROM agents a
            LEFT JOIN drafts d ON a.id = d.agent_id
            GROUP BY a.id, a.name, a.enabled, a.updated_at
            ORDER BY draft_count DESC
            LIMIT {limit}
            """
        )

        agents_data = []
        for row in results:
            # 处理 last_run 时间（从字符串转换为datetime）
            last_run = None
            if row["last_run"]:
                try:
                    # SQLite返回的是字符串，需要转换为datetime
                    if isinstance(row["last_run"], str):
                        last_run = datetime.fromisoformat(row["last_run"])
                    else:
                        last_run = row["last_run"]
                except:
                    last_run = None

            agents_data.append({
                "id": row["id"],
                "name": row["name"],
                "enabled": bool(row["enabled"]),
                "draftCount": row["draft_count"] or 0,
                "totalInteractions": (row["draft_count"] or 0) * 100,  # TODO: 实际互动数
                "lastRun": format_time_ago(last_run) if last_run else "从未运行"
            })

        return agents_data
    except Exception as e:
        logger.error(f"获取热门Agent失败: {str(e)}", exc_info=True)
        return []


def format_time(dt: datetime) -> str:
    """格式化时间为相对时间"""
    if not dt:
        return "未知"

    # 如果 dt 有时区信息，确保它和当前时间都是 UTC
    if dt.tzinfo is not None:
        # 获取当前 UTC 时间
        now = datetime.now(timezone.utc)
        # dt 已经是 UTC 时间（+00:00）
        diff = (now - dt).total_seconds()
    else:
        # 如果 dt 无时区，假设是 UTC
        now = datetime.now()
        diff = (now - dt).total_seconds()

    if diff < 60:
        return f"{int(diff)}秒前"
    elif diff < 3600:
        return f"{int(diff/60)}分钟前"
    elif diff < 86400:
        return f"{int(diff/3600)}小时前"
    else:
        return f"{int(diff/86400)}天前"


def format_time_ago(dt: datetime) -> str:
    """格式化时间差"""
    if not dt:
        return "无"

    now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
    diff = now - dt

    if diff.seconds < 60:
        return f"{diff.seconds}秒前"
    elif diff.seconds < 3600:
        return f"{diff.seconds // 60}分钟前"
    elif diff.days == 0:
        return f"{diff.seconds // 3600}小时前"
    elif diff.days < 7:
        return f"{diff.days}天前"
    else:
        return dt.strftime("%Y-%m-%d")
