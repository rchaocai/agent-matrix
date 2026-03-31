"""
Agent模型
"""

from tortoise import fields
from tortoise.models import Model


class Agent(Model):
    """Agent配置表"""

    id = fields.CharField(max_length=50, pk=True)
    name = fields.CharField(max_length=100)
    enabled = fields.BooleanField(default=True)
    config = fields.TextField(description="YAML格式的配置")
    account_id = fields.CharField(max_length=50, null=True, description="绑定的账户ID")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "agents"
        ordering = ["created_at"]

    def __str__(self):
        return f"Agent({self.id}, {self.name})"
