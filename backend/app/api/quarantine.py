"""隔离区管理"""
import os
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import get_current_user
from ..models import QuarantineFile
from ..response import ok, fail, page_data
from ..upload_util import abs_path_of

router = APIRouter(prefix="/quarantine", tags=["隔离区"])


@router.get("/page")
def list_files(page: int = 1, pageSize: int = 10, keyword: str | None = None,
               risk_level: str | None = None, status: str | None = None,
               db: Session = Depends(get_db), current=Depends(get_current_user)):
    q = db.query(QuarantineFile)
    if keyword:
        q = q.filter(QuarantineFile.file_name.like(f"%{keyword}%"))
    if risk_level:
        q = q.filter(QuarantineFile.risk_level == risk_level)
    if status:
        q = q.filter(QuarantineFile.status == status)
    total = q.count()
    rows = q.order_by(QuarantineFile.id.desc()).offset((page - 1) * pageSize).limit(pageSize).all()
    return ok(page_data([{
        "id": r.id, "file_name": r.file_name, "origin_path": r.origin_path,
        "quarantine_path": r.quarantine_path, "file_hash": r.file_hash,
        "file_size": r.file_size, "hit_rule": r.hit_rule,
        "risk_level": r.risk_level, "status": r.status,
        "task_id": r.task_id, "create_time": r.create_time,
    } for r in rows], total, page, pageSize))


@router.put("/restore/{qid}")
def restore(qid: int, db: Session = Depends(get_db), current=Depends(get_current_user)):
    f = db.query(QuarantineFile).get(qid)
    if not f:
        return fail("记录不存在")
    f.status = "restored"
    db.commit()
    return ok(msg="已标记恢复")


@router.delete("/delete/{qid}")
def delete_q(qid: int, db: Session = Depends(get_db), current=Depends(get_current_user)):
    f = db.query(QuarantineFile).get(qid)
    if not f:
        return fail("记录不存在")
    # 物理删除隔离副本
    try:
        p = abs_path_of(f.quarantine_path) if f.quarantine_path else None
        if p and os.path.exists(p):
            os.remove(p)
    except Exception:
        pass
    f.status = "deleted"
    db.commit()
    return ok(msg="已彻底删除")
