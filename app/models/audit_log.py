"""
审计日志模型
"""

from tortoise import fields
from tortoise.models import Model
from datetime import datetime
import uuid


class AuditLog(Model):
    """审计日志表（记录所有敏感操作）"""

    id = fields.CharField(max_length=50, pk=True)
    action = fields.CharField(max_length=100)  # login, logout, create_agent, delete_agent, etc.
    resource_type = fields.CharField(max_length=50, null=True)  # agent, draft, account, etc.
    resource_id = fields.CharField(max_length=50, null=True)
    details = fields.JSONField(null=True)
    ip_address = fields.CharField(max_length=50, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    # 关联用户（会自动创建 user_id 字段）
    user: fields.ForeignKeyRelation['User'] = fields.ForeignKeyField(
        'models.User', related_name='audit_logs', to_field='id', null=True
    )

    class Meta:
        table = "audit_logs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"AuditLog({self.action}, {self.resource_type})"

    @classmethod
    def generate_id(cls):
        """生成审计日志ID"""
        return f"audit_{uuid.uuid4().hex[:12]}"
