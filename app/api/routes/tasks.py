"""
Task执行历史API路由
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.models import Task
from datetime import datetime
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


class TaskResponse(BaseModel):
    """Task响应模型"""
    id: int
    agent_id: str
    agent_name: Optional[str] = None
    status: str
    started_at: str
    completed_at: Optional[str] = None
    result: Optional[dict] = None
    error: Optional[str] = None
    skill_results: List[dict] = []
    metadata: dict = {}


@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    agent_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=20, le=100)
):
    """获取Task执行历史列表"""
    query = Task.all()

    if agent_id:
        query = query.filter(agent_id=agent_id)
    if status:
        query = query.filter(status=status)

    tasks = await query.limit(limit).order_by("-started_at")

    result = []
    for t in tasks:
        # 处理result字段（可能是字符串、dict或无效格式）
        result_value = t.result
        if result_value is not None:
            if isinstance(result_value, str):
                try:
                    import json
                    result_value = json.loads(result_value)
                except json.JSONDecodeError:
                    result_value = {"raw": str(result_value)}
            elif not isinstance(result_value, dict):
                result_value = {"value": result_value}
        else:
            result_value = None

        # 处理skill_results字段（可能是字符串、list或无效格式）
        skill_results_value = t.skill_results
        if skill_results_value is not None:
            if isinstance(skill_results_value, str):
                try:
                    import json
                    skill_results_value = json.loads(skill_results_value)
                except json.JSONDecodeError:
                    skill_results_value = []
            elif not isinstance(skill_results_value, list):
                skill_results_value = []
        else:
            skill_results_value = []

        # 处理metadata字段（可能是字符串、dict或无效格式）
        metadata_value = t.metadata
        if metadata_value is not None:
            if isinstance(metadata_value, str):
                try:
                    import json
                    metadata_value = json.loads(metadata_value)
                except json.JSONDecodeError:
                    metadata_value = {}
            elif not isinstance(metadata_value, dict):
                metadata_value = {}
        else:
            metadata_value = {}

        result.append(TaskResponse(
            id=t.id,
            agent_id=t.agent_id,
            agent_name=t.agent_name,
            status=t.status,
            started_at=t.started_at.isoformat() if t.started_at else None,
            completed_at=t.completed_at.isoformat() if t.completed_at else None,
            result=result_value,
            error=t.error,
            skill_results=skill_results_value,
            metadata=metadata_value
        ))
    return result


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int):
    """获取指定Task详情"""
    task = await Task.get_or_none(id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task不存在")

    # 处理result字段（可能是字符串、dict或无效格式）
    result_value = task.result
    if result_value is not None:
        if isinstance(result_value, str):
            try:
                import json
                result_value = json.loads(result_value)
            except json.JSONDecodeError:
                result_value = {"raw": str(result_value)}
        elif not isinstance(result_value, dict):
            result_value = {"value": result_value}
    else:
        result_value = None

    # 处理skill_results字段（可能是字符串、list或无效格式）
    skill_results_value = task.skill_results
    if skill_results_value is not None:
        if isinstance(skill_results_value, str):
            try:
                import json
                skill_results_value = json.loads(skill_results_value)
            except json.JSONDecodeError:
                skill_results_value = []
        elif not isinstance(skill_results_value, list):
            skill_results_value = []
    else:
        skill_results_value = []

    # 处理metadata字段（可能是字符串、dict或无效格式）
    metadata_value = task.metadata
    if metadata_value is not None:
        if isinstance(metadata_value, str):
            try:
                import json
                metadata_value = json.loads(metadata_value)
            except json.JSONDecodeError:
                metadata_value = {}
        elif not isinstance(metadata_value, dict):
            metadata_value = {}
    else:
        metadata_value = {}

    return TaskResponse(
        id=task.id,
        agent_id=task.agent_id,
        agent_name=task.agent_name,
        status=task.status,
        started_at=task.started_at.isoformat() if task.started_at else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        result=result_value,
        error=task.error,
        skill_results=skill_results_value,
        metadata=metadata_value
    )


@router.delete("/{task_id}")
async def delete_task(task_id: int):
    """删除指定Task"""
    task = await Task.get_or_none(id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task不存在")

    await task.delete()
    return {"message": "Task删除成功"}


@router.delete("/")
async def delete_tasks_by_agent(agent_id: str, status: Optional[str] = None):
    """批量删除指定Agent的Task"""
    query = Task.filter(agent_id=agent_id)

    if status:
        query = query.filter(status=status)

    count = await query.count()
    await query.delete()

    return {"message": f"已删除 {count} 个Task"}
