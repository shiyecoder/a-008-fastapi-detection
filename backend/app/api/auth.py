"""认证相关：登录、注册、当前用户信息"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..database import get_db
from ..models import SysUser, SysUserRole, SysRole, SysRoleMenu, SysMenu
from ..security import hash_password, verify_password, create_token
from ..response import ok, fail
from ..deps import get_current_user

router = APIRouter(prefix="/auth", tags=["认证"])


class LoginIn(BaseModel):
    username: str
    password: str


class RegisterIn(BaseModel):
    username: str
    password: str
    nickname: str | None = None
    email: str | None = None
    phone: str | None = None


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(SysUser).filter(SysUser.username == body.username).first()
    if not user:
        return fail("用户不存在")
    if user.status != 1:
        return fail("用户已被禁用")
    if not verify_password(body.password, user.password):
        return fail("密码错误")
    token = create_token(user.id, user.username)
    return ok({"token": token, "userId": user.id, "username": user.username})


@router.post("/register")
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if db.query(SysUser).filter(SysUser.username == body.username).first():
        return fail("用户名已存在")
    user = SysUser(
        username=body.username,
        password=hash_password(body.password),
        nickname=body.nickname or body.username,
        email=body.email,
        phone=body.phone,
        status=1,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    # 默认分配普通用户角色（role_code=user）
    role = db.query(SysRole).filter(SysRole.role_code == "user").first()
    if role:
        db.add(SysUserRole(user_id=user.id, role_id=role.id))
        db.commit()
    return ok({"id": user.id})


def _build_menu_tree(menus: list) -> list:
    """构建菜单树"""
    nodes = {m.id: {
        "id": m.id, "parentId": m.parent_id, "name": m.name, "path": m.path,
        "component": m.component, "icon": m.icon, "sort": m.sort,
        "menuType": m.menu_type, "perms": m.perms, "visible": m.visible,
        "children": []
    } for m in menus if m.menu_type == 1 and m.visible == 1}
    roots = []
    for nid, n in nodes.items():
        pid = n["parentId"]
        if pid == 0 or pid not in nodes:
            roots.append(n)
        else:
            nodes[pid]["children"].append(n)
    # 排序
    def sort_tree(arr):
        arr.sort(key=lambda x: x["sort"])
        for x in arr:
            sort_tree(x["children"])
    sort_tree(roots)
    return roots


@router.get("/info")
def get_info(current=Depends(get_current_user), db: Session = Depends(get_db)):
    """获取当前登录用户信息+角色+菜单+权限"""
    # 角色
    role_ids = [ur.role_id for ur in db.query(SysUserRole).filter(SysUserRole.user_id == current.id).all()]
    roles = db.query(SysRole).filter(SysRole.id.in_(role_ids)).all() if role_ids else []
    role_codes = [r.role_code for r in roles]

    # 菜单：admin 拥有全部，其他根据角色-菜单关联
    if "admin" in role_codes:
        menus = db.query(SysMenu).all()
    else:
        menu_ids = set()
        if role_ids:
            for rm in db.query(SysRoleMenu).filter(SysRoleMenu.role_id.in_(role_ids)).all():
                menu_ids.add(rm.menu_id)
        menus = db.query(SysMenu).filter(SysMenu.id.in_(list(menu_ids))).all() if menu_ids else []

    perms = [m.perms for m in menus if m.perms]
    menu_tree = _build_menu_tree(menus)

    return ok({
        "userId": current.id,
        "username": current.username,
        "nickname": current.nickname,
        "email": current.email,
        "phone": current.phone,
        "avatar": current.avatar,
        "roles": role_codes,
        "perms": perms,
        "menus": menu_tree,
    })


@router.post("/logout")
def logout():
    return ok(msg="已退出")
