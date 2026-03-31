"""
数据库初始化脚本
"""

import asyncio
from tortoise import Tortoise
from app.config import settings
from pathlib import Path


async def init_db():
    """初始化数据库"""
    # 创建数据目录
    Path(settings.data_dir).mkdir(parents=True, exist_ok=True)

    # 初始化数据库连接
    await Tortoise.init(
        db_url=settings.database_url,
        modules={'models': ['app.models.agent', 'app.models.content',
                           'app.models.task', 'app.models.draft']}
    )

    # 生成数据库表
    await Tortoise.generate_schemas()
    print("数据库初始化完成")

    # 关闭连接
    await Tortoise.close_connections()


if __name__ == '__main__':
    asyncio.run(init_db())
