"""
内容管理API路由
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.models import Content
from pydantic import BaseModel


router = APIRouter()


class ContentResponse(BaseModel):
    """内容响应模型"""
    id: int
    agent_id: str
    source_type: str
    title: Optional[str]
    content: str
    collected_at: str


@router.get("/", response_model=List[ContentResponse])
async def list_content(
    agent_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """获取内容列表"""
    query = Content.all()
    if agent_id:
        query = query.filter(agent_id=agent_id)

    contents = await query.limit(limit).offset(offset)
    return [
        ContentResponse(
            id=c.id,
            agent_id=c.agent_id,
            source_type=c.source_type,
            title=c.title,
            content=c.content[:200] + "..." if len(c.content) > 200 else c.content,
            collected_at=c.collected_at.isoformat()
        )
        for c in contents
    ]


@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(content_id: int):
    """获取指定内容详情"""
    content = await Content.get_or_none(id=content_id)
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")
    return ContentResponse(
        id=content.id,
        agent_id=content.agent_id,
        source_type=content.source_type,
        title=content.title,
        content=content.content,
        collected_at=content.collected_at.isoformat()
    )
