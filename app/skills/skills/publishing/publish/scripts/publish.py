"""
发布内容到平台
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime, timezone

from app.publishers.xiaohongshu_publisher import publish_to_xiaohongshu


logger = logging.getLogger(__name__)


async def publish_content(
    title: str,
    content: str,
    images: List[str],
    platform: str = "xiaohongshu",
    account_id: Optional[str] = None,
    cookie: Optional[str] = None,
    topics: Optional[List[str]] = None,
    location: Optional[str] = None,
    headless: bool = True,
    draft_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    发布内容到指定平台

    Args:
        title: 标题
        content: 正文内容
        images: 图片路径列表
        platform: 平台名称
        account_id: 账号ID
        cookie: 登录凭证
        topics: 话题标签
        location: 地理位置
        headless: 是否无头模式
        draft_id: 草稿ID（用于更新状态）

    Returns:
        发布结果
    """
    try:
        # 验证图片文件是否存在
        valid_images = []
        for img_path in images:
            if Path(img_path).exists():
                valid_images.append(img_path)
            else:
                logger.warning(f"图片不存在，跳过: {img_path}")

        if not valid_images:
            return {
                'success': False,
                'error': '没有有效的图片文件',
                'code': 'no_images'
            }

        logger.info(f"开始发布到 {platform}: {title}")

        # 根据平台选择发布器
        if platform == "xiaohongshu":
            result = await publish_to_xiaohongshu(
                title=title,
                content=content,
                images=valid_images,
                cookie=cookie,
                headless=headless,
                topics=topics,
                location=location
            )

            # 发布成功后更新草稿状态
            if result.get('success') and draft_id:
                await update_draft_status(draft_id, platform)

            return result

        else:
            return {
                'success': False,
                'error': f'不支持的平台: {platform}',
                'code': 'unsupported_platform'
            }

    except Exception as e:
        logger.error(f"发布失败: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'code': 'publish_error'
        }


async def update_draft_status(draft_id: int, platform: str):
    """
    更新草稿状态为已发布

    Args:
        draft_id: 草稿ID
        platform: 平台名称
    """
    try:
        from tortoise import Tortoise
        from app.config import settings
        from app.models import Draft

        # 确保数据库已初始化
        if not Tortoise._inited:
            await Tortoise.init(
                db_url=settings.database_url,
                modules={'models': ['app.models.draft']}
            )

        # 查找并更新草稿
        draft = await Draft.get_or_none(id=draft_id)
        if draft:
            draft.status = 'published'
            draft.published_at = datetime.now(timezone.utc)
            await draft.save()
            logger.info(f"草稿 {draft_id} 状态已更新为 published")

    except Exception as e:
        logger.error(f"更新草稿状态失败: {str(e)}", exc_info=True)


def publish_content_sync(
    title: str,
    content: str,
    images: List[str],
    platform: str = "xiaohongshu",
    account_id: Optional[str] = None,
    cookie: Optional[str] = None,
    topics: Optional[List[str]] = None,
    location: Optional[str] = None,
    headless: bool = True
) -> Dict[str, Any]:
    """
    同步版本的发布函数

    Args:
        同 publish_content()

    Returns:
        发布结果
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None:
        # 在已有的事件循环中运行
        import concurrent.futures
        import threading

        result = []
        exception = []

        def run_in_new_loop():
            try:
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                task = publish_content(
                    title=title,
                    content=content,
                    images=images,
                    platform=platform,
                    account_id=account_id,
                    cookie=cookie,
                    topics=topics,
                    location=location,
                    headless=headless
                )
                result.append(new_loop.run_until_complete(task))
                new_loop.close()
            except Exception as e:
                exception.append(e)

        thread = threading.Thread(target=run_in_new_loop)
        thread.start()
        thread.join()

        if exception:
            raise exception[0]
        return result[0]
    else:
        # 没有事件循环，创建新的
        return asyncio.run(publish_content(
            title=title,
            content=content,
            images=images,
            platform=platform,
            account_id=account_id,
            cookie=cookie,
            topics=topics,
            location=location,
            headless=headless
        ))
