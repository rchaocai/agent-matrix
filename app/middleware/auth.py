"""
认证中间件
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging

from app.core.auth import get_current_user_from_token
from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    认证中间件

    验证所有非公开端点的请求
    """

    # 公开端点白名单
    OPEN_PATHS = [
        "/api/auth/login",
        "/api/auth/register",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/static",
        "/health",
        "/"
    ]

    async def dispatch(self, request: Request, call_next):
        """处理请求"""
        path = request.url.path

        # 检查是否是公开端点
        if any(path.startswith(open_path) for open_path in self.OPEN_PATHS):
            return await call_next(request)

        # OPTIONS请求（CORS预检）
        if request.method == "OPTIONS":
            return await call_next(request)

        try:
            # 验证Token并获取用户
            user = await get_current_user_from_token(
                authorization=request.headers.get("Authorization"),
                access_token=request.cookies.get("access_token")
            )

            # 将用户信息附加到request state
            request.state.user = user

            return await call_next(request)

        except HTTPException as exc:
            # 返回401错误
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail}
            )
        except Exception as exc:
            logger.error(f"认证中间件错误: {str(exc)}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "认证服务异常"}
            )


def log_request_middleware(app):
    """请求日志中间件工厂函数"""
    @app.middleware("http")
    async def log_request(request: Request, call_next):
        """记录所有请求"""
        logger.info(f"{request.method} {request.url.path}")

        response = await call_next(request)

        return response

    return log_request
