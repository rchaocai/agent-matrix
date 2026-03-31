"""
创建默认管理员用户
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.user import User
from app.core.security import get_password_hash
from tortoise import Tortoise


async def create_admin_user():
    """创建默认管理员用户"""

    # 初始化数据库连接
    await Tortoise.init(
        db_url='sqlite://data/database.db',
        modules={'models': ['app.models.user', 'app.models.agent',
                           'app.models.content', 'app.models.task',
                           'app.models.draft']}
    )

    # 检查是否已存在 admin 用户
    admin_exists = await User.filter(username='admin').exists()

    if admin_exists:
        print("Admin 用户已存在，跳过创建")
        admin = await User.get(username='admin')
        print(f"Admin 用户信息: {admin.username}, 角色: {admin.role}")
    else:
        # 创建 admin 用户
        admin_id = User.generate_id()
        await User.create(
            id=admin_id,
            username='admin',
            email='admin@example.com',
            password_hash=get_password_hash('admin123'),
            role='admin'
        )
        print(f"✅ Admin 用户创建成功！")
        print(f"   用户名: admin")
        print(f"   密码: admin123")
        print(f"   邮箱: admin@example.com")

    # 关闭连接
    await Tortoise.close_connections()


if __name__ == '__main__':
    asyncio.run(create_admin_user())
