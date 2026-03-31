"""
Draft模型
"""

from tortoise import fields
from tortoise.models import Model


class Draft(Model):
    """草稿表"""

    id = fields.IntField(pk=True)
    agent_id = fields.CharField(max_length=50)
    platform = fields.CharField(max_length=50, description="平台: xiaohongshu, douyin")
    title = fields.CharField(max_length=200, null=True)
    content = fields.TextField()
    image_paths = fields.TextField(null=True, description="图片路径，逗号分隔")
    tags = fields.JSONField(null=True, description="标签列表")
    status = fields.CharField(max_length=20, default="pending",
                            description="pending, pending_review, approved, published, failed")
    created_at = fields.DatetimeField(auto_now_add=True)
    published_at = fields.DatetimeField(null=True)

    class Meta:
        table = "drafts"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Draft({self.id}, {self.platform}, {self.status})"
