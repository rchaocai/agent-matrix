"""
提示词模板管理API路由
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.models import PromptTemplate
from pydantic import BaseModel
from datetime import datetime


router = APIRouter()


class PromptTemplateResponse(BaseModel):
    """提示词模板响应模型"""
    id: str
    name: str
    description: str
    category: str
    template_content: str
    variables: List[str]
    example_output: Optional[str] = None
    is_active: bool
    created_at: str
    updated_at: str


class PromptTemplateCreate(BaseModel):
    """创建提示词模板请求模型"""
    id: str
    name: str
    description: str
    category: str = "general"
    template_content: str
    variables: List[str] = []
    example_output: Optional[str] = None
    is_active: bool = True


class PromptTemplateUpdate(BaseModel):
    """更新提示词模板请求模型"""
    id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    template_content: Optional[str] = None
    variables: Optional[List[str]] = None
    example_output: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("/", response_model=List[PromptTemplateResponse])
async def list_templates(category: Optional[str] = None, active_only: bool = False):
    """获取所有提示词模板"""
    query = PromptTemplate.all()

    if category:
        query = query.filter(category=category)
    if active_only:
        query = query.filter(is_active=True)

    templates = await query.order_by("category", "name")

    return [
        PromptTemplateResponse(
            id=t.id,
            name=t.name,
            description=t.description,
            category=t.category,
            template_content=t.template_content,
            variables=t.variables or [],
            example_output=t.example_output,
            is_active=t.is_active,
            created_at=t.created_at.isoformat(),
            updated_at=t.updated_at.isoformat()
        )
        for t in templates
    ]


@router.get("/{template_id}", response_model=PromptTemplateResponse)
async def get_template(template_id: str):
    """获取指定提示词模板"""
    template = await PromptTemplate.get_or_none(id=template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    return PromptTemplateResponse(
        id=template.id,
        name=template.name,
        description=template.description,
        category=template.category,
        template_content=template.template_content,
        variables=template.variables or [],
        example_output=template.example_output,
        is_active=template.is_active,
        created_at=template.created_at.isoformat(),
        updated_at=template.updated_at.isoformat()
    )


@router.post("/", response_model=PromptTemplateResponse)
async def create_template(data: PromptTemplateCreate):
    """创建新提示词模板"""
    # 检查ID是否已存在
    existing = await PromptTemplate.get_or_none(id=data.id)
    if existing:
        raise HTTPException(status_code=400, detail="模板ID已存在")

    template = await PromptTemplate.create(
        id=data.id,
        name=data.name,
        description=data.description,
        category=data.category,
        template_content=data.template_content,
        variables=data.variables,
        example_output=data.example_output,
        is_active=data.is_active
    )

    return PromptTemplateResponse(
        id=template.id,
        name=template.name,
        description=template.description,
        category=template.category,
        template_content=template.template_content,
        variables=template.variables or [],
        example_output=template.example_output,
        is_active=template.is_active,
        created_at=template.created_at.isoformat(),
        updated_at=template.updated_at.isoformat()
    )


@router.put("/{template_id}", response_model=PromptTemplateResponse)
async def update_template(template_id: str, data: PromptTemplateUpdate):
    """更新提示词模板"""
    template = await PromptTemplate.get_or_none(id=template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    # 如果要修改ID，先检查新ID是否已被其他模板使用
    if data.id is not None and data.id != template_id:
        existing = await PromptTemplate.get_or_none(id=data.id)
        if existing:
            raise HTTPException(status_code=400, detail="模板ID已存在")
        template.id = data.id

    # 更新字段
    if data.name is not None:
        template.name = data.name
    if data.description is not None:
        template.description = data.description
    if data.category is not None:
        template.category = data.category
    if data.template_content is not None:
        template.template_content = data.template_content
    if data.variables is not None:
        template.variables = data.variables
    if data.example_output is not None:
        template.example_output = data.example_output
    if data.is_active is not None:
        template.is_active = data.is_active

    await template.save()

    return PromptTemplateResponse(
        id=template.id,
        name=template.name,
        description=template.description,
        category=template.category,
        template_content=template.template_content,
        variables=template.variables or [],
        example_output=template.example_output,
        is_active=template.is_active,
        created_at=template.created_at.isoformat(),
        updated_at=template.updated_at.isoformat()
    )


@router.delete("/{template_id}")
async def delete_template(template_id: str):
    """删除提示词模板"""
    template = await PromptTemplate.get_or_none(id=template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    await template.delete()
    return {"message": f"模板 {template_id} 已删除"}


@router.post("/{template_id}/duplicate", response_model=PromptTemplateResponse)
async def duplicate_template(template_id: str):
    """复制提示词模板"""
    template = await PromptTemplate.get_or_none(id=template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    # 生成新的ID：在原ID后添加 _copy 后缀
    new_id = f"{template_id}_copy"

    # 检查新ID是否已存在
    counter = 1
    while await PromptTemplate.get_or_none(id=new_id):
        new_id = f"{template_id}_copy{counter}"
        counter += 1

    # 复制模板
    new_template = await PromptTemplate.create(
        id=new_id,
        name=f"{template.name} (副本)",
        description=template.description,
        category=template.category,
        template_content=template.template_content,
        variables=template.variables,
        example_output=template.example_output,
        is_active=True
    )

    return PromptTemplateResponse(
        id=new_template.id,
        name=new_template.name,
        description=new_template.description,
        category=new_template.category,
        template_content=new_template.template_content,
        variables=new_template.variables or [],
        example_output=new_template.example_output,
        is_active=new_template.is_active,
        created_at=new_template.created_at.isoformat(),
        updated_at=new_template.updated_at.isoformat()
    )


@router.get("/categories/list")
async def list_categories():
    """获取所有模板分类"""
    categories = await PromptTemplate.all().distinct().values("category")
    return {
        "categories": [c["category"] for c in categories]
    }
