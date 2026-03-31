"""
用户模型
"""

from tortoise import fields
from tortoise.models import Model
from datetime import datetime
import uuid


class User(Model):
    """用户表"""

    id = fields.CharField(max_length=50, pk=True)
    username = fields.CharField(max_length=50, unique=True)
    email = fields.CharField(max_length=100, unique=True)
    password_hash = fields.CharField(max_length=255)
    role = fields.CharField(max_length=20, default='user')  # admin, user
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    last_login_at = fields.DatetimeField(null=True)

    class Meta:
        table = "users"
        ordering = ["created_at"]

    def __str__(self):
        return f"User({self.username}, {self.role})"

    @classmethod
    def generate_id(cls):
        """生成用户ID"""
        return f"user_{uuid.uuid4().hex[:12]}"
