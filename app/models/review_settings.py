"""
审核设置模型
"""

from tortoise import fields
from tortoise.models import Model


class ReviewSettings(Model):
    """审核设置表"""

    id = fields.IntField(pk=True)
    sensitive_word_enabled = fields.BooleanField(default=True, description="启用敏感词检测")
    sensitive_categories = fields.JSONField(default=['politics', 'porn', 'violence'], description="检测类别")
    custom_words = fields.TextField(null=True, description="自定义敏感词，换行分隔")
    quality_score_enabled = fields.BooleanField(default=True, description="启用质量评分")
    min_quality_score = fields.IntField(default=60, description="最低质量阈值")
    weights = fields.JSONField(default={'readability': 30, 'completeness': 40, 'attractiveness': 30}, description="评分权重")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "review_settings"

    def __str__(self):
        return f"ReviewSettings({self.id})"

    @classmethod
    async def get_settings(cls) -> "ReviewSettings":
        """获取审核设置（单例模式）"""
        settings = await cls.first()
        if not settings:
            settings = await cls.create()
        return settings
