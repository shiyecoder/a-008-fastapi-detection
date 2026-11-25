"""菜单管理"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import get_current_user
from ..models import SysMenu, SysRoleMenu
from ..response import ok, fail

router = APIRouter(prefix="/menu", tags=["菜单管理"])


class MenuIn(BaseModel):
    parent_id: int = 0
    name: str
    path: str | None = None
    component: str | None = None
    icon: str | None = None
    sort: int = 0
    menu_type: int = 1
    perms: str | None = None
    visible: int = 1


def _build_tree(menus):
    nodes = {m.id: {
        "id": m.id, "parent_id": m.parent_id, "name": m.name, "path": m.path,
        "component": m.component, "icon": m.icon, "sort": m.sort,
        "menu_type": m.menu_type, "perms": m.perms, "visible": m.visible,
        "create_time": m.create_time, "children": []
    } for m in menus}
    roots = []
    for nid, n in nodes.items():
        pid = n["parent_id"]
        if pid == 0 or pid not in nodes:
            roots.append(n)
        else:
            nodes[pid]["children"].append(n)
    def sort_tree(arr):
        arr.sort(key=lambda x: x["sort"])
        for x in arr:
            sort_tree(x["children"])
    sort_tree(roots)
    return roots


@router.get("/tree")
def menu_tree(db: Session = Depends(get_db), current=Depends(get_current_user)):
    """所有菜单树（用于菜单管理 + 角色分配菜单）"""
    menus = db.query(SysMenu).all()
    return ok(_build_tree(menus))


@router.post("/add")
def add_menu(body: MenuIn, db: Session = Depends(get_db), current=Depends(get_current_user)):
    m = SysMenu(**body.model_dump())
    db.add(m)
    db.commit()
    return ok({"id": m.id})


@router.put("/update/{mid}")
def update_menu(mid: int, body: MenuIn, db: Session = Depends(get_db), current=Depends(get_current_user)):
    m = db.query(SysMenu).get(mid)
    if not m:
        return fail("菜单不存在")
    for k, v in body.model_dump().items():
        setattr(m, k, v)
    db.commit()
    return ok(msg="修改成功")


@router.delete("/delete/{mid}")
def del_menu(mid: int, db: Session = Depends(get_db), current=Depends(get_current_user)):
    m = db.query(SysMenu).get(mid)
    if not m:
        return fail("菜单不存在")
    if db.query(SysMenu).filter(SysMenu.parent_id == mid).first():
        return fail("存在子菜单，无法删除")
    db.query(SysRoleMenu).filter(SysRoleMenu.menu_id == mid).delete()
    db.delete(m)
    db.commit()
    return ok(msg="删除成功")
