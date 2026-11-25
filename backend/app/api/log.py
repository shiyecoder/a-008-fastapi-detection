"""操作日志"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import get_current_user
from ..models import SysLog
from ..response import ok, page_data, fail

router = APIRouter(prefix="/log", tags=["操作日志"])


@router.get("/page")
def list_logs(page: int = 1, pageSize: int = 10, keyword: str | None = None,
              module: str | None = None,
              db: Session = Depends(get_db), current=Depends(get_current_user)):
    q = db.query(SysLog)
    if keyword:
        q = q.filter(SysLog.username.like(f"%{keyword}%"))
    if module:
        q = q.filter(SysLog.module == module)
    total = q.count()
    rows = q.order_by(SysLog.id.desc()).offset((page - 1) * pageSize).limit(pageSize).all()
    return ok(page_data([{
        "id": r.id, "user_id": r.user_id, "username": r.username,
        "module": r.module, "operation": r.operation, "method": r.method,
        "url": r.url, "ip": r.ip, "status": r.status, "create_time": r.create_time,
    } for r in rows], total, page, pageSize))


@router.delete("/delete/{lid}")
def del_log(lid: int, db: Session = Depends(get_db), current=Depends(get_current_user)):
    r = db.query(SysLog).get(lid)
    if not r:
        return fail("不存在")
    db.delete(r)
    db.commit()
    return ok(msg="删除成功")


@router.delete("/clear")
def clear_logs(db: Session = Depends(get_db), current=Depends(get_current_user)):
    db.query(SysLog).delete()
    db.commit()
    return ok(msg="日志已清空")
