"""
账号模型
用于管理发布平台账号（小红书、抖音等）
"""

from tortoise import fields
from tortoise.models import Model


class Account(Model):
    """平台账号模型"""

    # 基础信息
    id = fields.CharField(max_length=50, pk=True)
    name = fields.CharField(max_length=100, description="账号名称")
    platform = fields.CharField(max_length=20, description="平台类型: xiaohongshu/douyin")

    # 账号状态
    enabled = fields.BooleanField(default=True, description="是否启用")
    status = fields.CharField(max_length=20, default="offline", description="账号状态: online/offline")

    # 登录信息
    phone = fields.CharField(max_length=20, null=True, description="绑定的手机号")
    login_type = fields.CharField(max_length=20, default="cookie", description="登录方式: cookie/qrcode/sms")
    cookie = fields.TextField(null=True, description="Cookie内容")

    # Agent绑定（JSON字段存储绑定的Agent ID列表）
    bound_agents = fields.JSONField(default=[], description="绑定的Agent ID列表")

    # 账号统计数据（从平台获取）
    followers = fields.IntField(default=0, description="粉丝数")
    today_posts = fields.IntField(default=0, description="今日发文数")
    total_posts = fields.IntField(default=0, description="总发文数")
    last_active = fields.CharField(max_length=50, null=True, description="最后活跃时间")

    # 时间戳
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "accounts"
        description = "平台账号表"
