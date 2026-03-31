"""
审核模型
用于内容审核记录
"""

from tortoise import fields
from tortoise.models import Model
from datetime import datetime


class Review(Model):
    """内容审核记录"""

    # 关联信息
    draft = fields.ForeignKeyField("models.Draft", related_name="reviews", on_delete=fields.CASCADE, null=True)
    agent_id = fields.CharField(max_length=50, description="Agent ID")

    # 审核状态
    status = fields.CharField(max_length=20, default="pending", description="审核状态: pending/approved/rejected")

    # 敏感词检测结果
    sensitive_word_count = fields.IntField(default=0, description="敏感词数量")
    sensitive_words = fields.JSONField(default=list, description="敏感词列表")
    risk_level = fields.CharField(max_length=20, default="low", description="风险等级: low/medium/high")

    # 质量评分
    quality_score = fields.IntField(default=0, description="总分(0-100)")
    readability_score = fields.IntField(default=0, description="可读性得分")
    completeness_score = fields.IntField(default=0, description="完整性得分")
    attractiveness_score = fields.IntField(default=0, description="吸引力得分")

    # 审核结果
    reviewer = fields.CharField(max_length=50, null=True, description="审核人（自动审核为system）")
    review_notes = fields.TextField(null=True, description="审核备注")
    reviewed_at = fields.DatetimeField(null=True, description="审核时间")

    # 时间戳
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "reviews"
        description = "内容审核记录表"
