"""安全相关：密码哈希 / JWT"""
from datetime import datetime, timedelta
import bcrypt
from jose import jwt, JWTError
from .config import settings


def hash_password(password: str) -> str:
    if isinstance(password, str):
        password = password.encode("utf-8")
    # bcrypt 限制 72 字节
    if len(password) > 72:
        password = password[:72]
    return bcrypt.hashpw(password, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        if isinstance(plain, str):
            plain = plain.encode("utf-8")
        if len(plain) > 72:
            plain = plain[:72]
        if isinstance(hashed, str):
            hashed = hashed.encode("utf-8")
        return bcrypt.checkpw(plain, hashed)
    except Exception:
        return False


def create_token(user_id: int, username: str) -> str:
    payload = {
        "uid": user_id,
        "username": username,
        "exp": datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None
