"""
认证核心模块
"""

from typing import Optional
from fastapi import Depends, HTTPException, status, Cookie
from starlette.requests import Request

from app.models.user import User
from app.models.session import Session
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token
)
from datetime import datetime, timedelta, timezone
import uuid
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """认证服务"""

    @staticmethod
    async def register(username: str, email: str, password: str) -> User:
        """
        用户注册

        Args:
            username: 用户名
            email: 邮箱
            password: 密码

        Returns:
            创建的用户对象

        Raises:
            HTTPException: 用户名或邮箱已存在
        """
        # 检查用户名是否存在
        existing_user = await User.get_or_none(username=username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )

        # 检查邮箱是否存在
        existing_email = await User.get_or_none(email=email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )

        # 创建用户
        user = await User.create(
            id=User.generate_id(),
            username=username,
            email=email,
            password_hash=get_password_hash(password),
            role="user"
        )

        logger.info(f"新用户注册成功: {username}")
        return user

    @staticmethod
    async def login(username: str, password: str) -> User:
        """
        用户登录

        Args:
            username: 用户名
            password: 密码

        Returns:
            用户对象

        Raises:
            HTTPException: 用户名或密码错误
        """
        user = await User.get_or_none(username=username)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )

        if not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )

        # 更新最后登录时间
        user.last_login_at = datetime.now(timezone.utc)
        await user.save()

        logger.info(f"用户登录成功: {username}")
        return user

    @staticmethod
    async def create_session(user: User, request: Request = None) -> dict:
        """
        创建会话

        Args:
            user: 用户对象
            request: 请求对象（用于获取IP）

        Returns:
            包含access_token和refresh_token的字典
        """
        # 生成Token
        access_token = create_access_token({"sub": user.id})
        refresh_token = create_refresh_token({"sub": user.id})

        # 获取客户端IP
        ip_address = None
        if request:
            ip_address = request.client.host

        # 保存会话到数据库
        session = await Session.create(
            id=Session.generate_id(),
            user_id=user.id,
            refresh_token=refresh_token,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7)
        )

        # 记录审计日志
        from app.models.audit_log import AuditLog
        await AuditLog.create(
            id=AuditLog.generate_id(),
            user_id=user.id,
            action="login",
            resource_type="user",
            resource_id=user.id,
            ip_address=ip_address
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
        }

    @staticmethod
    async def refresh_token(refresh_token_str: str) -> str:
        """
        刷新Access Token

        Args:
            refresh_token_str: Refresh Token

        Returns:
            新的Access Token

        Raises:
            HTTPException: Refresh Token无效或已过期
        """
        # 验证Token格式
        payload = verify_token(refresh_token_str, token_type="refresh")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh Token无效或已过期"
            )

        user_id = payload.get("sub")

        # 检查会话是否存在
        session = await Session.get_or_none(refresh_token=refresh_token_str)
        if not session or session.is_expired():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh Token无效或已过期"
            )

        # 生成新的Access Token
        access_token = create_access_token({"sub": user_id})

        logger.info(f"Token刷新成功: user_id={user_id}")
        return access_token

    @staticmethod
    async def logout(refresh_token_str: str, user_id: str) -> None:
        """
        用户登出

        Args:
            refresh_token_str: Refresh Token
            user_id: 用户ID
        """
        # 删除会话
        if refresh_token_str:
            session = await Session.get_or_none(refresh_token=refresh_token_str)
            if session:
                await session.delete()

        # 记录审计日志
        from app.models.audit_log import AuditLog
        await AuditLog.create(
            id=AuditLog.generate_id(),
            user_id=user_id,
            action="logout",
            resource_type="user",
            resource_id=user_id
        )

        logger.info(f"用户登出: user_id={user_id}")

    @staticmethod
    async def get_current_user(token: str) -> Optional[User]:
        """
        从Token获取当前用户

        Args:
            token: Access Token

        Returns:
            用户对象或None
        """
        payload = verify_token(token, token_type="access")
        if not payload:
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        user = await User.get_or_none(id=user_id)
        return user


# 依赖注入函数
async def get_current_user_from_token(
    authorization: str = None,
    access_token: str = Cookie(None)
) -> User:
    """
    从请求中获取当前用户（依赖注入）

    Args:
        authorization: Authorization header
        access_token: Cookie中的token

    Returns:
        当前用户

    Raises:
        HTTPException: 未认证或Token无效
    """
    # 优先从Authorization header获取
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    elif access_token:
        token = access_token

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未认证",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user = await AuthService.get_current_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token无效或已过期",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user_from_token)
) -> User:
    """
    获取当前管理员用户（依赖注入）

    Args:
        current_user: 当前用户

    Returns:
        当前管理员用户

    Raises:
        HTTPException: 权限不足
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限"
        )

    return current_user


# 可选的认证（允许未登录访问）
async def get_optional_user(
    authorization: str = None,
    access_token: str = Cookie(None)
) -> Optional[User]:
    """
    可选认证（不强制要求登录）

    Returns:
        用户对象或None
    """
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    elif access_token:
        token = access_token

    if not token:
        return None

    return await AuthService.get_current_user(token)
