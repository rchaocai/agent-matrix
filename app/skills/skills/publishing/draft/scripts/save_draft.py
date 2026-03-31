"""
草稿保存脚本
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
from dotenv import load_dotenv
env_path = project_root / '.env'
if env_path.exists():
    load_dotenv(env_path)

from tortoise import Tortoise
from app.models import Draft
from app.config import settings


async def save_draft(
    agent_id: str,
    platform: str,
    content: str,
    title: str = None,
    images: str = None,
    tags: list = None,
    metadata: str = None
) -> dict:
    """
    保存草稿到数据库

    Args:
        agent_id: Agent ID
        platform: 目标平台
        content: 正文内容
        title: 标题
        images: 图片路径（逗号分隔）
        tags: 标签列表
        metadata: 元数据（JSON字符串）

    Returns:
        保存结果
    """
    try:
        # 确保数据库已初始化
        if not Tortoise._inited:
            await Tortoise.init(
                db_url=settings.database_url,
                modules={'models': ['app.models.draft']}
            )

        # 解析元数据
        metadata_dict = {}
        if metadata:
            try:
                metadata_dict = json.loads(metadata)
            except json.JSONDecodeError:
                return {
                    'error': 'metadata字段必须是有效的JSON格式',
                    'status': 'failed'
                }

        # 创建草稿
        draft = await Draft.create(
            agent_id=agent_id,
            platform=platform,
            title=title,
            content=content,
            image_paths=images,
            tags=tags,
            status='pending',
            metadata=metadata_dict
        )

        return {
            'draft_id': draft.id,
            'status': 'saved',
            'created_at': draft.created_at.isoformat(),
            'platform': platform,
            'tags': tags,
            'message': '草稿保存成功'
        }

    except Exception as e:
        return {
            'error': str(e),
            'status': 'failed'
        }


async def list_drafts(agent_id: str = None, platform: str = None, limit: int = 20):
    """
    列出草稿

    Args:
        agent_id: Agent ID（可选）
        platform: 平台（可选）
        limit: 返回数量
    """
    try:
        # 确保数据库已初始化
        if not Tortoise._inited:
            await Tortoise.init(
                db_url=settings.database_url,
                modules={'models': ['app.models.draft']}
            )

        query = Draft.all()

        if agent_id:
            query = query.filter(agent_id=agent_id)
        if platform:
            query = query.filter(platform=platform)

        drafts = await query.limit(limit).order_by('-created_at')

        result = []
        for draft in drafts:
            result.append({
                'id': draft.id,
                'agent_id': draft.agent_id,
                'platform': draft.platform,
                'title': draft.title,
                'content': draft.content[:100] + '...' if len(draft.content) > 100 else draft.content,
                'status': draft.status,
                'created_at': draft.created_at.isoformat()
            })

        return {
            'drafts': result,
            'total': len(result)
        }

    except Exception as e:
        return {
            'error': str(e),
            'drafts': [],
            'total': 0
        }


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='草稿保存工具')
    parser.add_argument('--action', default='save',
                       choices=['save', 'list'],
                       help='操作类型')

    # 保存草稿的参数
    parser.add_argument('--agent-id', help='Agent ID')
    parser.add_argument('--platform', help='目标平台')
    parser.add_argument('--title', help='内容标题')
    parser.add_argument('--content', help='正文内容')
    parser.add_argument('--images', help='图片路径（逗号分隔）')
    parser.add_argument('--metadata', help='元数据（JSON格式）')

    # 列出草稿的参数
    parser.add_argument('--filter-agent', help='过滤Agent ID')
    parser.add_argument('--filter-platform', help='过滤平台')
    parser.add_argument('--limit', type=int, default=20, help='返回数量')

    args = parser.parse_args()

    if args.action == 'save':
        # 保存草稿
        if not args.agent_id or not args.platform or not args.content:
            print(json.dumps({
                'error': '保存草稿需要 --agent-id, --platform, --content 参数',
                'status': 'failed'
            }, ensure_ascii=False, indent=2))
            return

        result = await save_draft(
            agent_id=args.agent_id,
            platform=args.platform,
            content=args.content,
            title=args.title,
            images=args.images,
            metadata=args.metadata
        )

    elif args.action == 'list':
        # 列出草稿
        result = await list_drafts(
            agent_id=args.filter_agent,
            platform=args.filter_platform,
            limit=args.limit
        )

    # 输出JSON结果
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 关闭数据库连接
    await Tortoise.close_connections()


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
