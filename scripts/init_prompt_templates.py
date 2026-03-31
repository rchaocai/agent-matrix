"""
初始化提示词模板
"""

import asyncio
import yaml
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from tortoise import Tortoise
from app.config import settings
from app.models import PromptTemplate


async def init_templates():
    """初始化默认提示词模板"""
    await Tortoise.init(
        db_url=settings.database_url,
        modules={'models': ['app.models.prompt_template']}
    )

    templates = [
        {
            "id": "zen_case",
            "name": "禅宗公案",
            "description": "生成禅宗公案相关的智慧内容，适合修行、禅修类账号",
            "category": "禅修",
            "template_content": """请生成一篇关于{topic}的适合小红书发布的图文内容，要求：
1. 内容精炼，正文字数在300-500字之间
2. 语言优美，适合社交媒体发布
3. 主题积极向上，能够引起读者共鸣
4. 添加适当的emoji增加可读性

输出格式要求（必须严格遵守）：
【标题】
使用简洁有力的标题，15-25字，能够吸引点击

正文内容
分段清晰，每段不超过100字，内容生动有趣

#标签1 #标签2 #标签3
在文末添加3-5个相关话题标签，使用#开头""",
            "variables": ["topic"],
            "example_output": """【禅修的智慧：在喧嚣中找回内心的宁静】

在这个快节奏的时代，我们常常被各种信息和压力包围...

✨ 禅修，不仅是打坐，更是一种生活态度。

🍃 学会在喧嚣中保持内心的宁静...

#禅修 #内心平静 #智慧人生"""
        },
        {
            "id": "caigen_tan",
            "name": "菜根谭智慧",
            "description": "以《菜根谭》为主题，结合现代生活场景解读人生智慧",
            "category": "禅修",
            "template_content": """请以《菜根谭》的智慧为主题，创作一篇关于{topic}的图文内容：

1. 引用《菜根谭》经典语录1-2句
2. 结合现代生活场景进行解读
3. 语言简练，富有哲理
4. 正文字数300-400字

输出格式：
【菜根谭智慧：标题】

正文内容...

#菜根谭 #人生智慧 #修身养性""",
            "variables": ["topic"],
            "example_output": """【菜根谭智慧：处世之道】

"宠辱不惊，看庭前花开花落；去留无意，望天上云卷云舒。"

《菜根谭》这句经典，道尽了人生的大智慧...

✨ 在顺境时不骄不躁，在逆境时不怨不尤...

#菜根谭 #人生智慧 #修身养性"""
        },
        {
            "id": "buddha_wisdom",
            "name": "佛学智慧",
            "description": "分享佛学经典语句和智慧，避免宗教说教，侧重人生启示",
            "category": "禅修",
            "template_content": """请生成一篇关于{topic}的佛学智慧图文内容：

1. 引用佛经经典语句
2. 用平实的语言讲解佛学智慧
3. 避免宗教说教，侧重人生启示
4. 正文字数300-400字

输出格式：
【佛学智慧：标题】

正文内容...

#佛学 #智慧 #修行""",
            "variables": ["topic"],
            "example_output": """【佛学智慧：活在当下】

"一切有为法，如梦幻泡影。"

《金刚经》提醒我们：世间万物皆无常...

✨ 不执着于得失，方能获得真正的自在...

#佛学 #智慧 #修行 #慈悲"""
        },
        {
            "id": "houhei_wisdom",
            "name": "厚黑学智慧",
            "description": "分享人性真相、职场潜规则和高情商话术，体现'看透不说透'的智慧",
            "category": "职场",
            "template_content": """你是一位深谙人情世故的厚黑学践行者，擅长用犀利的视角解读社交潜规则。

请根据主题"{topic}"，创作一篇适合小红书发布的图文内容。

【内容要求】
1. 开篇用真实场景或案例切入，引发共鸣
2. 中段分析人性/职场逻辑，揭示隐藏规则
3. 结尾给出实用建议，强调自我保护
4. 全文体现"看透不说透"的智慧
5. 语言犀利但不刻薄，有分寸感

【输出格式】
【标题】
用两段式标题，前段制造反差，后段点出价值

正文内容（300-400字）
- 用emoji分隔观点（🎭🗝️🌙✨等）
- 每段不超过80字，便于阅读
- 适当使用"潜规则"、"人性"等关键词

#厚黑学 #职场潜规则 #高情商 #人性真相""",
            "variables": ["topic"],
            "example_output": """【送礼送不对，再好心意也白费】

🎭 真相1：礼多人不怪，但礼重了吓人
职场新人送的3000元礼品，让领导直接退回...

🗝️ 规则：日常小事常走动，关键时刻看情况
一杯奶茶、一盒特产，比贵重礼物更安全。

🌙 核心：送礼不是买人情，是表达心意
让对方收得安心，比价格更重要。

#厚黑学 #高情商 #职场潜规则"""
        }
    ]

    for template_data in templates:
        existing = await PromptTemplate.get_or_none(id=template_data["id"])
        if existing:
            print(f"⏭️  模板已存在: {template_data['id']} - {template_data['name']}")
        else:
            await PromptTemplate.create(**template_data)
            print(f"✅ 模板已创建: {template_data['id']} - {template_data['name']}")

    await Tortoise.close_connections()
    print("\n🎉 提示词模板初始化完成！")


if __name__ == "__main__":
    asyncio.run(init_templates())
