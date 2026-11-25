"""依赖注入：当前登录用户"""
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session
from .database import get_db
from .security import decode_token
from .models import SysUser


def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
) -> SysUser:
    """从请求头解析 JWT 并返回当前用户"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录或Token无效")
    token = authorization[len("Bearer "):].strip()
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token已过期或无效")
    user = db.query(SysUser).filter(SysUser.id == payload.get("uid")).first()
    if not user or user.status != 1:
        raise HTTPException(status_code=401, detail="用户不存在或已禁用")
    return user
