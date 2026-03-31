"""
认证API端点
"""

from fastapi import APIRouter, HTTPException, status, Response, Request, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging

from app.models.user import User
from app.models.session import Session
from app.core.auth import AuthService, get_current_user_from_token, get_current_admin

logger = logging.getLogger(__name__)

router = APIRouter()


# ====== 请求/响应模型 ======

class RegisterRequest(BaseModel):
    """注册请求"""
    username: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    """用户信息响应"""
    id: str
    username: str
    email: str
    role: str
    created_at: str
    last_login_at: Optional[str] = None


# ====== API端点 ======

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    request: Request,
    response: Response
):
    """
    用户注册

    创建新用户账号并返回认证Token
    """
    try:
        # 验证密码长度
        if len(data.password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="密码长度至少6位"
            )

        # 检查密码字节长度（bcrypt限制72字节）
        password_bytes = data.password.encode('utf-8')
        if len(password_bytes) > 72:
            # 计算可用的字符数
            if all(ord(c) < 128 for c in data.password):
                # 纯ASCII字符
                max_chars = 72
                detail = f"密码过长（{len(data.password)}个字符），最多支持{max_chars}个字符"
            else:
                # 包含非ASCII字符（如中文）
                max_chinese_chars = 24  # 72字节 / 3字节每字符
                detail = f"密码过长（约{len(password_bytes)}字节），最多支持约{max_chinese_chars}个中文字符或{72}个英文字符"

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=detail
            )

        # 注册用户
        user = await AuthService.register(
            username=data.username,
            email=data.email,
            password=data.password
        )

        # 创建会话
        tokens = await AuthService.create_session(user, request)

        # 设置httpOnly Cookie
        response.set_cookie(
            key="access_token",
            value=tokens["access_token"],
            httponly=True,
            max_age=15 * 60,  # 15分钟
            secure=False,  # 生产环境设为True（HTTPS）
            samesite="lax"
        )

        response.set_cookie(
            key="refresh_token",
            value=tokens["refresh_token"],
            httponly=True,
            max_age=7 * 24 * 60 * 60,  # 7天
            secure=False,
            samesite="lax"
        )

        return tokens

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"注册失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败，请稍后重试"
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    request: Request,
    response: Response
):
    """
    用户登录

    验证用户凭据并返回认证Token
    """
    try:
        # 登录验证
        user = await AuthService.login(
            username=data.username,
            password=data.password
        )

        # 创建会话
        tokens = await AuthService.create_session(user, request)

        # 设置httpOnly Cookie
        response.set_cookie(
            key="access_token",
            value=tokens["access_token"],
            httponly=True,
            max_age=15 * 60,
            secure=False,
            samesite="lax"
        )

        response.set_cookie(
            key="refresh_token",
            value=tokens["refresh_token"],
            httponly=True,
            max_age=7 * 24 * 60 * 60,
            secure=False,
            samesite="lax"
        )

        return tokens

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登录失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败，请稍后重试"
        )


@router.post("/refresh")
async def refresh_token(
    request: Request,
    response: Response,
    refresh_token: str = None
):
    """
    刷新Access Token

    使用Refresh Token获取新的Access Token
    """
    try:
        # 尝试从Cookie获取
        if not refresh_token:
            refresh_token = request.cookies.get("refresh_token")
        
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未提供Refresh Token"
            )

        # 刷新Token
        access_token = await AuthService.refresh_token(refresh_token)

        # 更新Cookie
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=15 * 60,
            secure=False,
            samesite="lax"
        )

        return {"access_token": access_token}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刷新Token失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="刷新Token失败"
        )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    refresh_token: str = None
):
    """
    用户登出

    清除会话并删除Cookie
    """
    try:
        # 从Authorization header获取当前用户
        auth_header = request.headers.get("Authorization")
        user_id = None

        if auth_header and auth_header.startswith("Bearer "):
            from app.core.auth import AuthService
            token = auth_header[7:]
            user_obj = await AuthService.get_current_user(token)
            if user_obj:
                user_id = user_obj.id

        # 删除会话
        if user_id and refresh_token:
            await AuthService.logout(refresh_token, user_id)

        # 清除Cookie
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")

        return {"message": "登出成功"}

    except Exception as e:
        logger.error(f"登出失败: {str(e)}", exc_info=True)
        # 即使失败也清除Cookie
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return {"message": "登出成功"}


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: User = Depends(get_current_user_from_token)
):
    """
    获取当前用户信息

    返回当前登录用户的详细信息
    """
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        created_at=current_user.created_at.isoformat(),
        last_login_at=current_user.last_login_at.isoformat() if current_user.last_login_at else None
    )


@router.post("/create-admin")
async def create_admin_user(
    username: str = "admin",
    password: str = "admin123",
    email: str = "admin@example.com"
):
    """
    创建管理员账户（初始化用）

    注意：生产环境使用后应删除此端点或修改密码
    """
    try:
        # 检查是否已存在admin用户
        existing = await User.get_or_none(username=username)
        if existing:
            return {
                "message": "管理员账户已存在",
                "username": username
            }

        # 创建管理员
        from app.core.security import get_password_hash
        admin = await User.create(
            id=User.generate_id(),
            username=username,
            email=email,
            password_hash=get_password_hash(password),
            role="admin"
        )

        return {
            "message": "管理员账户创建成功",
            "username": username,
            "password": password,
            "note": "请尽快修改默认密码"
        }

    except Exception as e:
        logger.error(f"创建管理员失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建管理员失败: {str(e)}"
        )
