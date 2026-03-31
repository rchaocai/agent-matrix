#!/usr/bin/env python3
"""迁移提示词模板数据：将字符串ID转换为UUID"""
import asyncio
import sqlite3
import uuid
from pathlib import Path

async def migrate_templates():
    """迁移提示词模板数据"""
    db_path = Path("data/database.db")

    if not db_path.exists():
        print("数据库文件不存在")
        return

    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 检查表结构
    cursor.execute("PRAGMA table_info(prompt_templates)")
    columns = cursor.fetchall()
    print("当前表结构:")
    for col in columns:
        print(f"  {col[1]}: {col[2]}")

    # 查询现有数据
    cursor.execute("SELECT id, name FROM prompt_templates")
    rows = cursor.fetchall()

    print(f"\n找到 {len(rows)} 条模板记录")

    # 检查是否有非UUID格式的ID
    invalid_ids = []
    for row in rows:
        template_id = row[0]
        try:
            uuid.UUID(template_id)
        except ValueError:
            invalid_ids.append((template_id, row[1]))

    if invalid_ids:
        print(f"\n发现 {len(invalid_ids)} 条需要迁移的记录:")
        for old_id, name in invalid_ids:
            print(f"  ID: {old_id}, 名称: {name}")

        # 为每条记录生成新的UUID
        for old_id, name in invalid_ids:
            new_id = str(uuid.uuid4())
            print(f"\n迁移: {old_id} -> {new_id}")

            # 更新ID
            cursor.execute(
                "UPDATE prompt_templates SET id = ? WHERE id = ?",
                (new_id, old_id)
            )

        # 提交更改
        conn.commit()
        print(f"\n✓ 迁移完成！")
    else:
        print("\n所有ID都是有效的UUID格式，无需迁移")

    conn.close()

if __name__ == "__main__":
    asyncio.run(migrate_templates())
