"""
添加数据库索引以提升查询性能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from tortoise import Tortoise
from app.config import settings


async def add_indexes():
    """添加数据库索引"""
    print("开始添加数据库索引...")

    # 初始化数据库连接
    await Tortoise.init(
        db_url=settings.database_url,
        modules={'models': ['app.models.agent', 'app.models.content',
                           'app.models.task', 'app.models.draft',
                           'app.models.account', 'app.models.review',
                           'app.models.user', 'app.models.session',
                           'app.models.audit_log']}
    )

    conn = Tortoise.get_connection("default")

    # 定义要创建的索引
    indexes = [
        # Drafts表索引
        "CREATE INDEX IF NOT EXISTS idx_drafts_agent_id ON drafts(agent_id);",
        "CREATE INDEX IF NOT EXISTS idx_drafts_status ON drafts(status);",
        "CREATE INDEX IF NOT EXISTS idx_drafts_platform ON drafts(platform);",
        "CREATE INDEX IF NOT EXISTS idx_drafts_created_at ON drafts(created_at DESC);",

        # Accounts表索引
        "CREATE INDEX IF NOT EXISTS idx_accounts_platform ON accounts(platform);",
        "CREATE INDEX IF NOT EXISTS idx_accounts_enabled ON accounts(enabled);",
        "CREATE INDEX IF NOT EXISTS idx_accounts_status ON accounts(status);",

        # Tasks表索引
        "CREATE INDEX IF NOT EXISTS idx_tasks_agent_id ON tasks(agent_id);",
        "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);",
        "CREATE INDEX IF NOT EXISTS idx_tasks_started_at ON tasks(started_at DESC);",

        # Reviews表索引
        "CREATE INDEX IF NOT EXISTS idx_reviews_status ON reviews(status);",
        "CREATE INDEX IF NOT EXISTS idx_reviews_draft_id ON reviews(draft);",
        "CREATE INDEX IF NOT EXISTS idx_reviews_created_at ON reviews(created_at DESC);",

        # Content表索引
        "CREATE INDEX IF NOT EXISTS idx_content_agent_id ON content(agent_id);",
        "CREATE INDEX IF NOT EXISTS idx_content_created_at ON content(created_at DESC);",

        # Users表索引
        "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);",
        "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
        "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);",

        # Sessions表索引
        "CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);",

        # AuditLogs表索引
        "CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);",
        "CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC);",
    ]

    # 创建索引
    success_count = 0
    for index_sql in indexes:
        try:
            await conn.execute_query(index_sql)
            success_count += 1
            print(f"✓ {index_sql[:80]}...")
        except Exception as e:
            print(f"✗ {index_sql[:80]}...")
            print(f"  错误: {e}")

    print(f"\n完成! 成功创建 {success_count}/{len(indexes)} 个索引")

    # 验证索引
    print("\n验证索引...")
    for table in ["drafts", "accounts", "tasks", "reviews", "content", "users", "sessions", "audit_logs"]:
        try:
            result = await conn.execute_query(f"PRAGMA index_list('{table}')")
            indexes_list = result[1] if result and result[1] else []
            print(f"  {table}: {len(indexes_list)} 个索引")
        except Exception as e:
            print(f"  {table}: 查询失败 - {e}")

    # 关闭连接
    await Tortoise.close_connections()
    print("\n数据库索引添加完成!")


if __name__ == "__main__":
    asyncio.run(add_indexes())
