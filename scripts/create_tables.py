"""
创建数据库表
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from tortoise import Tortoise
from app.config import settings


async def create_tables():
    """创建所有数据库表"""
    await Tortoise.init(
        db_url=settings.database_url,
        modules={'models': ['app.models.prompt_template']}
    )

    # 生成表结构
    await Tortoise.generate_schemas()

    print("✅ 数据库表创建完成！")

    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(create_tables())
