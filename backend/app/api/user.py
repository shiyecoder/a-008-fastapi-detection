"""用户管理"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_
from ..database import get_db
from ..deps import get_current_user
from ..models import SysUser, SysUserRole, SysRole
from ..response import ok, fail, page_data
from ..security import hash_password

router = APIRouter(prefix="/user", tags=["用户管理"])


class UserCreate(BaseModel):
    username: str
    password: str = "123456"
    nickname: str | None = None
    email: str | None = None
    phone: str | None = None
    status: int = 1
    remark: str | None = None
    role_ids: list[int] = []


class UserUpdate(BaseModel):
    nickname: str | None = None
    email: str | None = None
    phone: str | None = None
    status: int | None = None
    remark: str | None = None
    role_ids: list[int] | None = None


def _user_with_roles(db: Session, u: SysUser) -> dict:
    role_ids = [ur.role_id for ur in db.query(SysUserRole).filter(SysUserRole.user_id == u.id).all()]
    roles = db.query(SysRole).filter(SysRole.id.in_(role_ids)).all() if role_ids else []
    return {
        "id": u.id, "username": u.username, "nickname": u.nickname,
        "email": u.email, "phone": u.phone, "avatar": u.avatar,
        "status": u.status, "remark": u.remark,
        "create_time": u.create_time, "update_time": u.update_time,
        "role_ids": role_ids,
        "role_names": [r.role_name for r in roles],
    }


@router.get("/page")
def list_users(
    page: int = 1, pageSize: int = 10,
    keyword: str | None = None,
    status: int | None = None,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    q = db.query(SysUser)
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(or_(SysUser.username.like(kw), SysUser.nickname.like(kw), SysUser.email.like(kw)))
    if status is not None:
        q = q.filter(SysUser.status == status)
    total = q.count()
    users = q.order_by(SysUser.id.desc()).offset((page - 1) * pageSize).limit(pageSize).all()
    return ok(page_data([_user_with_roles(db, u) for u in users], total, page, pageSize))


@router.post("/add")
def add_user(body: UserCreate, db: Session = Depends(get_db), current=Depends(get_current_user)):
    if db.query(SysUser).filter(SysUser.username == body.username).first():
        return fail("用户名已存在")
    u = SysUser(
        username=body.username, password=hash_password(body.password),
        nickname=body.nickname or body.username, email=body.email, phone=body.phone,
        status=body.status, remark=body.remark,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    for rid in body.role_ids or []:
        db.add(SysUserRole(user_id=u.id, role_id=rid))
    db.commit()
    return ok({"id": u.id})


@router.put("/update/{uid}")
def update_user(uid: int, body: UserUpdate, db: Session = Depends(get_db), current=Depends(get_current_user)):
    u = db.query(SysUser).get(uid)
    if not u:
        return fail("用户不存在")
    for f in ("nickname", "email", "phone", "status", "remark"):
        v = getattr(body, f)
        if v is not None:
            setattr(u, f, v)
    if body.role_ids is not None:
        db.query(SysUserRole).filter(SysUserRole.user_id == uid).delete()
        for rid in body.role_ids:
            db.add(SysUserRole(user_id=uid, role_id=rid))
    db.commit()
    return ok(msg="修改成功")


@router.delete("/delete/{uid}")
def delete_user(uid: int, db: Session = Depends(get_db), current=Depends(get_current_user)):
    u = db.query(SysUser).get(uid)
    if not u:
        return fail("用户不存在")
    if u.username == "admin":
        return fail("不能删除超级管理员")
    db.query(SysUserRole).filter(SysUserRole.user_id == uid).delete()
    db.delete(u)
    db.commit()
    return ok(msg="删除成功")


@router.put("/reset-password/{uid}")
def reset_password(uid: int, db: Session = Depends(get_db), current=Depends(get_current_user)):
    u = db.query(SysUser).get(uid)
    if not u:
        return fail("用户不存在")
    u.password = hash_password("123456")
    db.commit()
    return ok(msg="密码已重置为 123456")
