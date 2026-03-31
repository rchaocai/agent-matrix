"""
安全工具模块
"""

from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt
from typing import Dict, Optional
import os
import logging
import bcrypt

logger = logging.getLogger(__name__)

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

# JWT配置
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码（使用bcrypt，与get_password_hash保持一致）"""
    try:
        # 将密码和哈希转换为字节
        password_bytes = plain_password.encode('utf-8')
        hash_bytes = hashed_password.encode('utf-8')

        # 使用bcrypt验证
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception as e:
        logger.error(f"密码验证失败: {str(e)}")
        return False


def get_password_hash(password: str) -> str:
    """生成密码哈希（直接使用bcrypt以支持长密码）"""
    try:
        # 将密码转换为字节
        password_bytes = password.encode('utf-8')

        # 检查密码长度
        if len(password_bytes) > 72:
            raise ValueError(
                f"密码过长（{len(password_bytes)}字节），"
                f"bcrypt算法限制最大72字节（约24个中文字符或72个英文字符）。"
                f"请缩短密码。"
            )

        # 使用bcrypt直接哈希
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    except ValueError:
        raise  # 重新抛出验证错误
    except Exception as e:
        logger.error(f"密码哈希失败: {str(e)}")
        raise


def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建Access Token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "type": "access"
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict) -> str:
    """创建Refresh Token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "type": "refresh"
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict]:
    """解码Token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


def verify_token(token: str, token_type: str = "access") -> Optional[Dict]:
    """验证Token并返回payload"""
    payload = decode_token(token)

    if not payload:
        return None

    # 检查Token类型
    if payload.get("type") != token_type:
        return None

    # 检查过期时间（JWT库会自动验证exp字段）
    return payload
