"""
迁移Task表，添加新字段
"""
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
env_path = project_root / '.env'
if env_path.exists():
    load_dotenv(env_path)

from tortoise import Tortoise
from app.models import Task


async def migrate():
    """执行迁移"""
    await Tortoise.init(
        db_url="sqlite://data/database.db",
        modules={"models": ["app.models"]}
    )

    # 获取数据库连接
    conn = Tortoise.get_connection("default")

    # 添加新字段
    try:
        await conn.execute_query_dict(
            "ALTER TABLE tasks ADD COLUMN agent_name VARCHAR(100)"
        )
        print("✅ 添加 agent_name 字段")
    except Exception as e:
        if "duplicate column" in str(e):
            print("⚠️  agent_name 字段已存在")
        else:
            print(f"❌ 添加 agent_name 失败: {e}")

    try:
        await conn.execute_query_dict(
            "ALTER TABLE tasks ADD COLUMN skill_results TEXT DEFAULT '[]'"
        )
        print("✅ 添加 skill_results 字段")
    except Exception as e:
        if "duplicate column" in str(e):
            print("⚠️  skill_results 字段已存在")
        else:
            print(f"❌ 添加 skill_results 失败: {e}")

    try:
        await conn.execute_query_dict(
            "ALTER TABLE tasks ADD COLUMN metadata TEXT DEFAULT '{}'"
        )
        print("✅ 添加 metadata 字段")
    except Exception as e:
        if "duplicate column" in str(e):
            print("⚠️  metadata 字段已存在")
        else:
            print(f"❌ 添加 metadata 失败: {e}")

    # 将result字段从TEXT改为JSON（SQLite不支持直接修改，需要重建表）
    print("📝 注意: result字段类型需要手动修改为JSON")

    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(migrate())
