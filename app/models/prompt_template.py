"""
提示词模板模型
"""

from tortoise import fields
from tortoise.models import Model


class PromptTemplate(Model):
    """提示词模板表"""

    id = fields.CharField(max_length=50, pk=True)
    name = fields.CharField(max_length=100, description="模板名称")
    description = fields.TextField(description="模板描述")
    category = fields.CharField(max_length=50, default="general", description="模板分类")
    template_content = fields.TextField(description="模板内容")
    variables = fields.JSONField(default=[], description="可用变量列表")
    example_output = fields.TextField(description="示例输出", null=True)
    is_active = fields.BooleanField(default=True, description="是否启用")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "prompt_templates"
        ordering = ["category", "name"]

    def __str__(self):
        return f"PromptTemplate({self.name})"
