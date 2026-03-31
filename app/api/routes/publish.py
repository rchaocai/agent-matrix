"""
发布 API 路由
提供内容发布到各平台的接口
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging

from app.publishers.xiaohongshu_publisher import XiaohongshuPublisher

logger = logging.getLogger(__name__)

router = APIRouter()


class PublishRequest(BaseModel):
    """发布请求模型"""

    title: str = Field(..., description="笔记标题")
    content: str = Field(..., description="笔记正文")
    images: List[str] = Field(..., description="图片路径列表")
    platform: str = Field(default="xiaohongshu", description="目标平台")
    account_id: str = Field(..., description="发布账号ID")
    topics: Optional[List[str]] = Field(default=None, description="话题标签")
    location: Optional[str] = Field(default=None, description="地理位置")
    headless: bool = Field(default=True, description="是否无头模式")
    draft_id: Optional[int] = Field(default=None, description="草稿ID（如果从草稿发布）")


class PublishResponse(BaseModel):
    """发布响应模型"""

    success: bool = Field(..., description="是否成功")
    message: Optional[str] = Field(default=None, description="提示信息")
    post_url: Optional[str] = Field(default=None, description="笔记URL")
    error: Optional[str] = Field(default=None, description="错误信息")


@router.post("/xiaohongshu", response_model=PublishResponse, summary="发布到小红书")
async def publish_to_xiaohongshu(request: PublishRequest, background_tasks: BackgroundTasks):
    """
    发布内容到小红书

    ## 功能说明
    - 自动登录小红书创作平台
    - 上传图片并填写内容
    - 添加话题标签和位置
    - 自动发布笔记

    ## 请求参数
    - **title**: 笔记标题
    - **content**: 笔记正文
    - **images**: 图片路径列表（绝对路径或相对路径）
    - **account_id**: 发布账号ID
    - **topics**: 话题标签（可选）
    - **location**: 地理位置（可选）
    - **headless**: 是否无头模式（默认true）

    ## 返回结果
    ```json
    {
      "success": true,
      "message": "发布成功",
      "post_url": "https://www.xiaohongshu.com/explore/..."
    }
    ```
    """
    try:
        # 从数据库获取账号信息（这里简化处理）
        # 实际应该查询 account 表获取 cookie
        from app.models.account import Account

        account = await Account.get_or_none(id=request.account_id, platform='xiaohongshu')
        if not account:
            raise HTTPException(status_code=404, detail=f"账号不存在: {request.account_id}")

        cookie = account.cookie

        if not cookie:
            return PublishResponse(
                success=False,
                error=f"账号「{account.name}」未配置Cookie，请先在账户管理页面扫码登录"
            )

        # 创建发布器并发布
        publisher = XiaohongshuPublisher()

        try:
            # 初始化
            logger.info(f"初始化浏览器，账号: {account.name}, cookie长度: {len(cookie) if cookie else 0}")
            await publisher.initialize(cookie_str=cookie, headless=request.headless)
            logger.info("浏览器初始化完成")

            # 检查登录状态
            logger.info("检查登录状态...")
            is_logged_in = await publisher.check_login_status()

            if not is_logged_in:
                logger.warning(f"账号「{account.name}」登录已失效")
                return PublishResponse(
                    success=False,
                    error=f"账号「{account.name}」登录已失效，请重新扫码登录"
                )

            logger.info("登录状态检查通过，开始发布...")

            # 发布内容
            result = await publisher.publish(
                title=request.title,
                content=request.content,
                images=request.images,
                topics=request.topics,
                location=request.location
            )

            # 如果是从草稿发布且发布成功，更新草稿状态
            if result.get('success') and request.draft_id:
                from app.models.draft import Draft
                from datetime import datetime, timezone

                draft = await Draft.get_or_none(id=request.draft_id)
                if draft:
                    draft.status = "published"
                    draft.published_at = datetime.now(timezone.utc)
                    await draft.save()
                    logger.info(f"草稿 {request.draft_id} 状态已更新为 published")

            return PublishResponse(
                success=result.get('success', False),
                message=result.get('message'),
                post_url=result.get('url'),
                error=result.get('error')
            )

        finally:
            await publisher.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"发布失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"发布失败: {str(e)}")


@router.post("/test-login", summary="测试登录状态")
async def test_login(account_id: str = Query(..., description="账号ID")):
    """
    测试账号登录状态

    ## 功能说明
    检查指定账号的登录状态是否有效

    ## 请求参数
    - **account_id**: 账号ID

    ## 返回结果
    ```json
    {
      "success": true,
      "logged_in": true,
      "message": "登录状态有效"
    }
    ```
    """
    try:
        from app.models.account import Account

        account = await Account.get_or_none(id=account_id, platform='xiaohongshu')
        if not account:
            raise HTTPException(status_code=404, detail=f"账号不存在: {account_id}")

        publisher = XiaohongshuPublisher()

        try:
            await publisher.initialize(cookie_str=account.cookie, headless=True)
            is_logged_in = await publisher.check_login_status()

            return {
                "success": True,
                "logged_in": is_logged_in,
                "message": "登录状态有效" if is_logged_in else "登录已失效"
            }

        finally:
            await publisher.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"测试登录失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"测试登录失败: {str(e)}")


@router.post("/qrcode-login", summary="二维码登录")
async def qrcode_login(
    account_id: str = Query(..., description="账号ID"),
    wait_time: int = Query(default=120, description="等待时间（秒）")
):
    """
    二维码登录

    ## 功能说明
    生成二维码供用户扫码登录，登录成功后保存Cookie

    ## 请求参数
    - **account_id**: 账号ID
    - **wait_time**: 等待扫码的时间（默认120秒）

    ## 返回结果
    ```json
    {
      "success": true,
      "message": "登录成功，Cookie已保存"
    }
    ```
    """
    publisher = None
    try:
        from app.models.account import Account

        logger.info(f"开始二维码登录流程，账号ID: {account_id}")

        # 检查账号是否存在
        account = await Account.get_or_none(id=account_id, platform='xiaohongshu')
        if not account:
            logger.error(f"账号不存在: {account_id}")
            return {
                "success": False,
                "message": f"账号不存在: {account_id}"
            }

        publisher = XiaohongshuPublisher()

        try:
            logger.info("初始化浏览器（非无头模式）...")
            await publisher.initialize(headless=False)
            logger.info("浏览器初始化成功")

            # 二维码登录
            logger.info("开始等待扫码...")
            success, cookie = await publisher.login_by_qrcode(wait_time=wait_time)

            logger.info(f"扫码登录结果: success={success}, cookie长度={len(cookie) if cookie else 0}")

            if success and cookie:
                # 保存cookie到数据库
                logger.info("保存Cookie到数据库...")
                account.cookie = cookie
                account.status = "online"
                await account.save()
                logger.info("Cookie保存成功")

                return {
                    "success": True,
                    "message": "登录成功，Cookie已保存"
                }
            else:
                logger.warning("登录失败或超时")
                return {
                    "success": False,
                    "message": "登录超时或失败，请重试"
                }

        except Exception as e:
            logger.error(f"扫码登录过程异常: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"登录失败: {str(e)}"
            }
        finally:
            if publisher:
                logger.info("关闭浏览器...")
                try:
                    await publisher.close()
                except Exception as e:
                    logger.error(f"关闭浏览器失败: {e}")

    except Exception as e:
        logger.error(f"二维码登录API异常: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": f"系统错误: {str(e)}"
        }


@router.get("/platforms", summary="获取支持的平台列表")
async def get_platforms():
    """
    获取支持的平台列表

    ## 返回结果
    ```json
    {
      "platforms": ["xiaohongshu"],
      "total": 1
    }
    """
    return {
        "platforms": ["xiaohongshu"],
        "total": 1,
        "coming_soon": ["douyin"]
    }
