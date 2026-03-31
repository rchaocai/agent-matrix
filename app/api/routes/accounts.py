"""
账号管理API路由
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.models import Account, Agent
from pydantic import BaseModel
from datetime import datetime
import uuid
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


async def get_account_agents(account) -> List[dict]:
    """获取账号绑定的Agent列表"""
    if not account.bound_agents:
        return []

    # 根据bound_agents列表查询Agent（不过滤enabled，显示所有绑定的Agent）
    agents = await Agent.filter(id__in=account.bound_agents).all()

    return [
        {
            "id": agent.id,
            "name": agent.name,
            "avatar": "🤖",
            "enabled": agent.enabled
        }
        for agent in agents
    ]


class AccountCreate(BaseModel):
    """创建账号请求模型"""
    name: str
    platform: str
    phone: Optional[str] = None
    login_type: str = "cookie"
    cookie: Optional[str] = None
    enabled: bool = True
    bound_agents: Optional[List[str]] = None  # 绑定的Agent ID列表


class AccountUpdate(BaseModel):
    """更新账号请求模型"""
    name: Optional[str] = None
    phone: Optional[str] = None
    cookie: Optional[str] = None
    session_data: Optional[dict] = None
    enabled: Optional[bool] = None
    bound_agents: Optional[List[str]] = None  # 绑定的Agent ID列表


class AccountResponse(BaseModel):
    """账号响应模型"""
    id: str
    name: str
    platform: str
    enabled: bool
    status: str
    phone: Optional[str]
    followers: int
    todayPosts: int
    totalPosts: int
    lastActive: Optional[str]
    createdAt: str
    updatedAt: str


@router.get("/")
async def list_accounts(
    platform: Optional[str] = None,
    enabled: Optional[bool] = None,
    limit: int = 50
):
    """获取账号列表"""
    from app.models import Draft
    from datetime import datetime, timedelta

    query = Account.all()

    if platform:
        query = query.filter(platform=platform)
    if enabled is not None:
        query = query.filter(enabled=enabled)

    accounts = await query.limit(limit).order_by("-created_at")

    # 使用北京时间计算今日
    now_local = datetime.now()
    today_local = now_local.date()
    today_start_local = datetime.combine(today_local, datetime.min.time())
    today_start_utc = today_start_local - timedelta(hours=8)

    # 获取每个账号的详细信息
    result = []
    for account in accounts:
        # 获取绑定的agents
        agents_list = await get_account_agents(account)

        # 从Draft表计算发文数
        # 获取该账号绑定的所有agent_id
        bound_agent_ids = account.bound_agents or []
        
        # 总发文数
        total_posts = 0
        today_posts = 0
        
        if bound_agent_ids:
            total_posts = await Draft.filter(
                agent_id__in=bound_agent_ids,
                status="published"
            ).count()
            
            # 今日发文数
            today_posts = await Draft.filter(
                agent_id__in=bound_agent_ids,
                status="published",
                created_at__gte=today_start_utc
            ).count()

        # 构建响应字典，添加hasCookie字段
        account_dict = {
            "id": account.id,
            "name": account.name,
            "platform": account.platform,
            "enabled": account.enabled,
            "status": account.status,
            "phone": account.phone,
            "login_type": account.login_type or "cookie",
            "cookie": account.cookie,
            "followers": account.followers or 0,
            "todayPosts": today_posts,
            "totalPosts": total_posts,
            "lastActive": account.last_active,
            "createdAt": account.created_at.isoformat(),
            "updatedAt": account.updated_at.isoformat(),
            "hasCookie": bool(account.cookie and len(str(account.cookie)) > 10),
            "agents": agents_list
        }

        result.append(account_dict)

    return result


@router.get("/{account_id}")
async def get_account(account_id: str):
    """获取账号详情"""
    from app.models import Account

    account = await Account.get_or_none(id=account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    return {
        "id": account.id,
        "name": account.name,
        "platform": account.platform,
        "enabled": account.enabled,
        "status": account.status,
        "phone": account.phone,
        "followers": account.followers,
        "todayPosts": account.today_posts,
        "totalPosts": account.total_posts,
        "lastActive": account.last_active,
        "createdAt": account.created_at.isoformat(),
        "updatedAt": account.updated_at.isoformat(),
        "hasCookie": bool(account.cookie and len(str(account.cookie)) > 10),
        "agents": await get_account_agents(account)
    }


@router.post("/")
async def create_account(data: AccountCreate):
    """创建新账号"""
    from app.models import Account

    # 自动生成账号ID
    account_id = f"acc_{uuid.uuid4().hex[:12]}"

    account = await Account.create(
        id=account_id,
        name=data.name,
        platform=data.platform,
        phone=data.phone,
        login_type=data.login_type,
        cookie=data.cookie,
        enabled=data.enabled,
        bound_agents=data.bound_agents or []
    )

    return {
        "id": account.id,
        "name": account.name,
        "platform": account.platform,
        "enabled": account.enabled,
        "status": account.status,
        "phone": account.phone,
        "followers": account.followers,
        "todayPosts": account.today_posts,
        "totalPosts": account.total_posts,
        "lastActive": account.last_active,
        "createdAt": account.created_at.isoformat(),
        "updatedAt": account.updated_at.isoformat(),
        "hasCookie": bool(account.cookie and len(str(account.cookie)) > 10),
        "agents": await get_account_agents(account)
    }


@router.put("/{account_id}")
async def update_account(account_id: str, data: AccountUpdate):
    """更新账号"""
    from app.models import Account

    account = await Account.get_or_none(id=account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    # 更新字段
    if data.name is not None:
        account.name = data.name
    if data.phone is not None:
        account.phone = data.phone
    if data.cookie is not None:
        account.cookie = data.cookie
    if data.session_data is not None:
        account.session_data = data.session_data
    if data.enabled is not None:
        account.enabled = data.enabled
    if data.bound_agents is not None:
        # 更新内存中的 Agent 实例（先清除旧绑定）
        from app.main import agent_manager
        if agent_manager:
            # 先获取当前绑定的 Agent（更新数据库前）
            old_bound_agents = await Agent.filter(account_id=account_id).values_list('id', flat=True)
            
            # 清除旧绑定的内存实例
            for agent_id in old_bound_agents:
                agent = agent_manager.get_agent(agent_id)
                if agent:
                    agent.account_id = None
                    logger.info(f"清除 Agent {agent_id} 的账户绑定")
        
        # 更新数据库：先清除所有绑定到此账户的 Agent
        await Agent.filter(account_id=account_id).update(account_id=None)
        
        # 再设置新绑定的 Agent
        if data.bound_agents:
            await Agent.filter(id__in=data.bound_agents).update(account_id=account_id)
        
        # 更新内存中的 Agent 实例（设置新绑定）
        if agent_manager and data.bound_agents:
            for agent_id in data.bound_agents:
                agent = agent_manager.get_agent(agent_id)
                if agent:
                    agent.account_id = account_id
                    logger.info(f"设置 Agent {agent_id} 绑定账户: {account_id}")
        
        account.bound_agents = data.bound_agents

    await account.save()

    return {
        "id": account.id,
        "name": account.name,
        "platform": account.platform,
        "enabled": account.enabled,
        "status": account.status,
        "phone": account.phone,
        "followers": account.followers,
        "todayPosts": account.today_posts,
        "totalPosts": account.total_posts,
        "lastActive": account.last_active,
        "createdAt": account.created_at.isoformat(),
        "updatedAt": account.updated_at.isoformat(),
        "hasCookie": bool(account.cookie and len(str(account.cookie)) > 10),
        "agents": await get_account_agents(account)
    }


@router.delete("/{account_id}")
async def delete_account(account_id: str):
    """删除账号"""
    from app.models import Account

    account = await Account.get_or_none(id=account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    await account.delete()
    return {"message": f"账号 {account_id} 已删除"}


@router.post("/{account_id}/refresh")
async def refresh_account(account_id: str):
    """刷新账号状态"""
    from app.models import Account
    import logging

    logger = logging.getLogger(__name__)

    account = await Account.get_or_none(id=account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    try:
        publisher = None

        if account.platform == "xiaohongshu":
            from app.publishers.xiaohongshu_publisher import XiaohongshuPublisher

            # 检查是否有cookie
            if not account.cookie or len(str(account.cookie)) < 10:
                return {
                    "message": f"账号「{account.name}」未配置Cookie",
                    "status": "offline",
                    "lastActive": account.last_active
                }

            publisher = XiaohongshuPublisher()

            # 测试登录状态
            await publisher.initialize(cookie_str=account.cookie, headless=True)
            is_logged_in = await publisher.check_login_status()

            account.last_active = datetime.now().strftime("%Y-%m-%d %H:%M")
            account.status = "online" if is_logged_in else "offline"
            await account.save()

            await publisher.close()

            logger.info(f"账号 {account.name} 状态刷新完成: {account.status}")

            return {
                "message": f"账号「{account.name}」状态已刷新",
                "status": account.status,
                "lastActive": account.last_active
            }
        else:
            # 其他平台暂不支持自动刷新
            logger.warning(f"平台 {account.platform} 暂不支持自动刷新状态")

            return {
                "message": f"平台「{account.platform}」暂不支持自动刷新",
                "status": account.status,
                "lastActive": account.last_active
            }

    except Exception as e:
        logger.error(f"刷新账号状态失败: {str(e)}", exc_info=True)
        account.status = "offline"
        account.last_active = datetime.now().strftime("%Y-%m-%d %H:%M")
        await account.save()

        return {
            "message": f"刷新失败: {str(e)}",
            "status": "offline",
            "lastActive": account.last_active
        }


@router.patch("/{account_id}/toggle")
async def toggle_account(account_id: str):
    """切换账号启用状态"""
    from app.models import Account

    account = await Account.get_or_none(id=account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    account.enabled = not account.enabled
    await account.save()

    return {
        "message": f"账号 {account_id} 已{'启用' if account.enabled else '禁用'}",
        "enabled": account.enabled
    }
