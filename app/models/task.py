"""
Task模型
"""

from tortoise import fields
from tortoise.models import Model
import json


class Task(Model):
    """任务执行记录表"""

    id = fields.IntField(pk=True)
    agent_id = fields.CharField(max_length=50)
    agent_name = fields.CharField(max_length=100, null=True)  # Agent名称快照
    status = fields.CharField(max_length=20, default="pending",
                            description="pending, running, completed, failed")
    started_at = fields.DatetimeField(null=True)
    completed_at = fields.DatetimeField(null=True)
    result = fields.TextField(null=True, description="任务结果JSON")
    error = fields.TextField(null=True, description="错误信息")
    skill_results = fields.TextField(default="[]", description="每个skill的执行结果")
    metadata = fields.TextField(default="{}", description="元数据")

    class Meta:
        table = "tasks"
        ordering = ["-started_at"]

    def __str__(self):
        return f"Task({self.id}, {self.agent_id}, {self.status})"
