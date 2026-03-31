"""
Content模型
"""

from tortoise import fields
from tortoise.models import Model


class Content(Model):
    """内容表"""

    id = fields.IntField(pk=True)
    agent_id = fields.CharField(max_length=50)
    source_type = fields.CharField(max_length=20, description="采集类型: rss, scraper, local")
    source_url = fields.CharField(max_length=500, null=True)
    title = fields.CharField(max_length=200, null=True)
    content = fields.TextField()
    metadata = fields.JSONField(default=dict, description="额外的元数据")
    collected_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "content"
        ordering = ["-collected_at"]

    def __str__(self):
        return f"Content({self.id}, {self.title})"
