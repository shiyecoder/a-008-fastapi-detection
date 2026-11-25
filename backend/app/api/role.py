"""角色管理 + 角色分配菜单"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import get_current_user
from ..models import SysRole, SysRoleMenu
from ..response import ok, fail, page_data

router = APIRouter(prefix="/role", tags=["角色管理"])


class RoleIn(BaseModel):
    role_name: str
    role_code: str
    status: int = 1
    remark: str | None = None


class AssignMenu(BaseModel):
    menu_ids: list[int] = []


@router.get("/page")
def list_roles(page: int = 1, pageSize: int = 10, keyword: str | None = None,
               db: Session = Depends(get_db), current=Depends(get_current_user)):
    q = db.query(SysRole)
    if keyword:
        q = q.filter(SysRole.role_name.like(f"%{keyword}%"))
    total = q.count()
    rows = q.order_by(SysRole.id.desc()).offset((page - 1) * pageSize).limit(pageSize).all()
    return ok(page_data([{
        "id": r.id, "role_name": r.role_name, "role_code": r.role_code,
        "status": r.status, "remark": r.remark, "create_time": r.create_time,
    } for r in rows], total, page, pageSize))


@router.get("/all")
def all_roles(db: Session = Depends(get_db), current=Depends(get_current_user)):
    rows = db.query(SysRole).filter(SysRole.status == 1).all()
    return ok([{"id": r.id, "role_name": r.role_name, "role_code": r.role_code} for r in rows])


@router.post("/add")
def add_role(body: RoleIn, db: Session = Depends(get_db), current=Depends(get_current_user)):
    if db.query(SysRole).filter(SysRole.role_code == body.role_code).first():
        return fail("角色编码已存在")
    r = SysRole(**body.model_dump())
    db.add(r)
    db.commit()
    return ok({"id": r.id})


@router.put("/update/{rid}")
def update_role(rid: int, body: RoleIn, db: Session = Depends(get_db), current=Depends(get_current_user)):
    r = db.query(SysRole).get(rid)
    if not r:
        return fail("角色不存在")
    for k, v in body.model_dump().items():
        setattr(r, k, v)
    db.commit()
    return ok(msg="修改成功")


@router.delete("/delete/{rid}")
def del_role(rid: int, db: Session = Depends(get_db), current=Depends(get_current_user)):
    r = db.query(SysRole).get(rid)
    if not r:
        return fail("角色不存在")
    if r.role_code == "admin":
        return fail("内置角色不可删除")
    db.query(SysRoleMenu).filter(SysRoleMenu.role_id == rid).delete()
    db.delete(r)
    db.commit()
    return ok(msg="删除成功")


@router.get("/menu/{rid}")
def get_role_menus(rid: int, db: Session = Depends(get_db), current=Depends(get_current_user)):
    """获取角色已分配的菜单ID列表"""
    rows = db.query(SysRoleMenu).filter(SysRoleMenu.role_id == rid).all()
    return ok([rm.menu_id for rm in rows])


@router.post("/assign-menu/{rid}")
def assign_menu(rid: int, body: AssignMenu, db: Session = Depends(get_db), current=Depends(get_current_user)):
    """为角色分配菜单"""
    db.query(SysRoleMenu).filter(SysRoleMenu.role_id == rid).delete()
    for mid in body.menu_ids:
        db.add(SysRoleMenu(role_id=rid, menu_id=mid))
    db.commit()
    return ok(msg="分配成功")
