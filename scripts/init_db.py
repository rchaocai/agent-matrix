"""
数据库初始化脚本
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from tortoise import Tortoise
from app.config import settings


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
