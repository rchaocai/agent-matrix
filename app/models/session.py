"""
会话模型
"""

from tortoise import fields
from tortoise.models import Model
from datetime import datetime
import uuid


class Session(Model):
    """会话表（用于Token黑名单和会话管理）"""

    id = fields.CharField(max_length=50, pk=True)
    refresh_token = fields.CharField(max_length=500, unique=True)
    expires_at = fields.DatetimeField()
    created_at = fields.DatetimeField(auto_now_add=True)

    # 关联用户（会自动创建 user_id 字段）
    user: fields.ForeignKeyRelation['User'] = fields.ForeignKeyField(
        'models.User', related_name='sessions', to_field='id'
    )

    class Meta:
        table = "sessions"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Session({self.user_id}, expires={self.expires_at})"

    @classmethod
    def generate_id(cls):
        """生成会话ID"""
        return f"session_{uuid.uuid4().hex[:12]}"

    def is_expired(self) -> bool:
        """检查会话是否过期"""
        from datetime import timezone
        now = datetime.now(timezone.utc)
        if self.expires_at.tzinfo is None:
            return datetime.now() > self.expires_at
        else:
            return now > self.expires_at
