"""
草稿管理API路由
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
from datetime import datetime, timezone
from app.models import Draft, Account
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


router = APIRouter()


class DraftCreate(BaseModel):
    """创建草稿请求模型"""
    agent_id: str
    platform: str
    title: str
    content: str
    image_paths: Optional[str] = None
    status: str = "pending"


class DraftUpdate(BaseModel):
    """更新草稿请求模型"""
    title: Optional[str] = None
    content: Optional[str] = None
    image_paths: Optional[str] = None
    status: Optional[str] = None


class DraftResponse(BaseModel):
    """草稿响应模型"""
    id: int
    agent_id: str
    agent_name: Optional[str] = None
    platform: str
    title: str
    content: str
    image_paths: Optional[str]
    tags: Optional[List[str]] = None
    status: str
    review_status: Optional[str] = None
    created_at: str
    published_at: Optional[str]


@router.get("/", response_model=List[DraftResponse])
async def list_drafts(
    agent_id: Optional[str] = None,
    platform: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
):
    """获取草稿列表"""
    from app.models import Agent, Review

    query = Draft.all()

    if agent_id:
        query = query.filter(agent_id=agent_id)
    if platform:
        query = query.filter(platform=platform)
    if status:
        query = query.filter(status=status)

    drafts = await query.limit(limit).order_by("-created_at")

    # 批量获取Agent信息
    agent_ids = list(set(d.agent_id for d in drafts))
    agents = await Agent.filter(id__in=agent_ids)
    agent_dict = {agent.id: agent.name for agent in agents}

    # 批量获取审核状态
    draft_ids = [d.id for d in drafts]
    reviews = await Review.filter(draft_id__in=draft_ids)
    review_dict = {r.draft_id: r.status for r in reviews}

    return [
        DraftResponse(
            id=d.id,
            agent_id=d.agent_id,
            agent_name=agent_dict.get(d.agent_id),
            platform=d.platform,
            title=d.title,
            content=d.content,
            image_paths=d.image_paths,
            tags=d.tags if isinstance(d.tags, list) and all(isinstance(t, str) for t in d.tags) else [],
            status=d.status,
            review_status=review_dict.get(d.id),
            created_at=d.created_at.isoformat(),
            published_at=d.published_at.isoformat() if d.published_at else None
        )
        for d in drafts
    ]


@router.get("/{draft_id}", response_model=DraftResponse)
async def get_draft(draft_id: int):
    """获取指定草稿详情"""
    from app.models import Agent, Review

    draft = await Draft.get_or_none(id=draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="草稿不存在")

    # 获取Agent名称
    agent = await Agent.get_or_none(id=draft.agent_id)
    agent_name = agent.name if agent else None

    # 获取审核状态
    review = await Review.get_or_none(draft_id=draft_id)
    review_status = review.status if review else None

    return DraftResponse(
        id=draft.id,
        agent_id=draft.agent_id,
        agent_name=agent_name,
        platform=draft.platform,
        title=draft.title,
        content=draft.content,
        image_paths=draft.image_paths,
        tags=draft.tags if isinstance(draft.tags, list) and all(isinstance(t, str) for t in draft.tags) else [],
        status=draft.status,
        review_status=review_status,
        created_at=draft.created_at.isoformat(),
        published_at=draft.published_at.isoformat() if draft.published_at else None
    )


@router.post("/", response_model=DraftResponse)
async def create_draft(data: DraftCreate):
    """创建新草稿"""
    draft = await Draft.create(
        agent_id=data.agent_id,
        platform=data.platform,
        title=data.title,
        content=data.content,
        image_paths=data.image_paths,
        status=data.status
    )

    return DraftResponse(
        id=draft.id,
        agent_id=draft.agent_id,
        platform=draft.platform,
        title=draft.title,
        content=draft.content,
        image_paths=draft.image_paths,
        status=draft.status,
        created_at=draft.created_at.isoformat(),
        published_at=None
    )


@router.put("/{draft_id}", response_model=DraftResponse)
async def update_draft(draft_id: int, data: DraftUpdate):
    """更新草稿"""
    draft = await Draft.get_or_none(id=draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="草稿不存在")

    # 更新字段
    if data.title is not None:
        draft.title = data.title
    if data.content is not None:
        draft.content = data.content
    if data.image_paths is not None:
        draft.image_paths = data.image_paths
    if data.status is not None:
        draft.status = data.status

    await draft.save()

    return DraftResponse(
        id=draft.id,
        agent_id=draft.agent_id,
        platform=draft.platform,
        title=draft.title,
        content=draft.content,
        image_paths=draft.image_paths,
        status=draft.status,
        created_at=draft.created_at.isoformat(),
        published_at=draft.published_at.isoformat() if draft.published_at else None
    )


@router.delete("/{draft_id}")
async def delete_draft(draft_id: int):
    """删除草稿"""
    draft = await Draft.get_or_none(id=draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="草稿不存在")

    await draft.delete()
    return {"message": f"草稿 {draft_id} 已删除"}


@router.post("/{draft_id}/publish")
async def publish_draft(draft_id: int, background_tasks: BackgroundTasks):
    """
    发布草稿到对应平台

    实际调用发布API进行发布
    """
    draft = await Draft.get_or_none(id=draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="草稿不存在")

    # 检查草稿状态
    if draft.status == "published":
        raise HTTPException(status_code=400, detail="草稿已发布")

    # 获取该平台的可用账号
    accounts = await Account.filter(
        platform=draft.platform,
        enabled=True
    ).all()

    if not accounts:
        raise HTTPException(
            status_code=400,
            detail=f"没有找到可用的{draft.platform}账号，请先添加账号"
        )

    # 使用第一个可用账号（可以优化为让用户选择）
    account = accounts[0]

    if not account.cookie:
        raise HTTPException(
            status_code=400,
            detail=f"账号 {account.name} 未配置Cookie，请先登录"
        )

    try:
        # 导入发布器
        from app.publishers.xiaohongshu_publisher import XiaohongshuPublisher

        # 解析图片路径
        images = []
        if draft.image_paths:
            images = draft.image_paths.split(',')

        if not images:
            raise HTTPException(
                status_code=400,
                detail="草稿没有图片，无法发布"
            )

        # 创建发布器并发布
        publisher = XiaohongshuPublisher()

        try:
            # 初始化（使用非无头模式以便调试）
            await publisher.initialize(cookie_str=account.cookie, headless=False)

            # 检查登录状态
            is_logged_in = await publisher.check_login_status()
            if not is_logged_in:
                raise HTTPException(
                    status_code=400,
                    detail="账号登录已失效，请重新登录"
                )

            # 发布内容
            result = await publisher.publish(
                title=draft.title or "无标题",
                content=draft.content,
                images=images
            )

            if not result.get('success'):
                # 发布失败，更新状态
                draft.status = "failed"
                await draft.save()

                raise HTTPException(
                    status_code=500,
                    detail=f"发布失败: {result.get('error', '未知错误')}"
                )

            # 发布成功，更新状态
            draft.status = "published"
            draft.published_at = datetime.now(timezone.utc)
            await draft.save()

            logger.info(f"草稿 {draft_id} 发布成功")

            return {
                "message": f"草稿 {draft_id} 已发布到 {draft.platform}",
                "post_url": result.get('url'),
                "account": account.name
            }

        finally:
            await publisher.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"发布草稿失败: {str(e)}", exc_info=True)

        # 更新草稿状态为失败
        draft.status = "failed"
        await draft.save()

        raise HTTPException(
            status_code=500,
            detail=f"发布失败: {str(e)}"
        )
