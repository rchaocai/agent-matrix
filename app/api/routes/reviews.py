"""
审核管理API路由
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.models import Review, Draft, Agent
from pydantic import BaseModel
from datetime import datetime


router = APIRouter()


class ReviewResponse(BaseModel):
    """审核记录响应模型"""
    id: int
    agent_id: str
    agent_name: Optional[str] = None
    draft_id: Optional[int] = None
    title: Optional[str] = None
    content: Optional[str] = None
    platform: Optional[str] = None
    status: str
    sensitive_word_count: int
    sensitive_words: list
    risk_level: str
    quality_score: int
    scores: dict
    created_at: str


@router.get("/", response_model=List[ReviewResponse])
async def list_reviews(
    agent_id: Optional[str] = None,
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    limit: int = 50
):
    """获取审核记录列表"""
    query = Review.all()

    if agent_id:
        query = query.filter(agent_id=agent_id)
    if status:
        query = query.filter(status=status)
    if risk_level:
        query = query.filter(risk_level=risk_level)

    reviews = await query.limit(limit).order_by("-created_at")

    result = []
    for r in reviews:
        # 获取 Agent 名称
        agent = await Agent.get_or_none(id=r.agent_id)
        agent_name = agent.name if agent else r.agent_id

        # 获取 Draft 信息
        draft = None
        title = None
        content = None
        platform = None
        if r.draft_id:
            draft = await Draft.get_or_none(id=r.draft_id)
            if draft:
                title = draft.title
                content = draft.content[:200] + '...' if len(draft.content) > 200 else draft.content
                platform = draft.platform

        result.append(ReviewResponse(
            id=r.id,
            agent_id=r.agent_id,
            agent_name=agent_name,
            draft_id=r.draft_id,
            title=title,
            content=content,
            platform=platform,
            status=r.status,
            sensitive_word_count=r.sensitive_word_count,
            sensitive_words=r.sensitive_words,
            risk_level=r.risk_level,
            quality_score=r.quality_score,
            scores={
                "readability": r.readability_score,
                "completeness": r.completeness_score,
                "attractiveness": r.attractiveness_score
            },
            created_at=r.created_at.isoformat()
        ))

    return result


@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(review_id: int):
    """获取审核详情"""
    review = await Review.get_or_none(id=review_id)
    if not review:
        raise HTTPException(status_code=404, detail="审核记录不存在")

    # 获取 Agent 名称
    agent = await Agent.get_or_none(id=review.agent_id)
    agent_name = agent.name if agent else review.agent_id

    # 获取 Draft 信息
    draft = None
    title = None
    content = None
    platform = None
    if review.draft_id:
        draft = await Draft.get_or_none(id=review.draft_id)
        if draft:
            title = draft.title
            content = draft.content
            platform = draft.platform

    return ReviewResponse(
        id=review.id,
        agent_id=review.agent_id,
        agent_name=agent_name,
        draft_id=review.draft_id,
        title=title,
        content=content,
        platform=platform,
        status=review.status,
        sensitive_word_count=review.sensitive_word_count,
        sensitive_words=review.sensitive_words,
        risk_level=review.risk_level,
        quality_score=review.quality_score,
        scores={
            "readability": review.readability_score,
            "completeness": review.completeness_score,
            "attractiveness": review.attractiveness_score
        },
        created_at=review.created_at.isoformat()
    )


@router.post("/{review_id}/approve")
async def approve_review(review_id: int):
    """通过审核"""
    review = await Review.get_or_none(id=review_id)
    if not review:
        raise HTTPException(status_code=404, detail="审核记录不存在")

    review.status = "approved"
    review.reviewed_at = datetime.now()
    review.reviewer = "system"
    await review.save()

    # 草稿状态保持 pending（待发布），不需要修改

    return {"message": f"审核记录 {review_id} 已通过"}


@router.post("/{review_id}/reject")
async def reject_review(review_id: int, notes: Optional[str] = None):
    """拒绝审核"""
    review = await Review.get_or_none(id=review_id)
    if not review:
        raise HTTPException(status_code=404, detail="审核记录不存在")

    review.status = "rejected"
    review.reviewed_at = datetime.now()
    review.reviewer = "system"
    review.review_notes = notes
    await review.save()

    # 更新关联的草稿状态
    if review.draft_id:
        draft = await Draft.get_or_none(id=review.draft_id)
        if draft:
            draft.status = "rejected"
            await draft.save()

    return {"message": f"审核记录 {review_id} 已拒绝"}


@router.post("/batch-approve")
async def batch_approve(review_ids: List[int]):
    """批量通过审核"""
    count = 0
    for review_id in review_ids:
        review = await Review.get_or_none(id=review_id)
        if review:
            review.status = "approved"
            review.reviewed_at = datetime.now()
            review.reviewer = "system"
            await review.save()

            # 草稿状态保持 pending（待发布），不需要修改

            count += 1

    return {"message": f"已批量通过 {count} 条审核记录"}


@router.post("/batch-reject")
async def batch_reject(review_ids: List[int], notes: Optional[str] = None):
    """批量拒绝审核"""
    count = 0
    for review_id in review_ids:
        review = await Review.get_or_none(id=review_id)
        if review:
            review.status = "rejected"
            review.reviewed_at = datetime.now()
            review.reviewer = "system"
            review.review_notes = notes
            await review.save()

            if review.draft_id:
                draft = await Draft.get_or_none(id=review.draft_id)
                if draft:
                    draft.status = "rejected"
                    await draft.save()

            count += 1

    return {"message": f"已批量拒绝 {count} 条审核记录"}
