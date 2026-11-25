"""告警中心"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from ..database import get_db
from ..deps import get_current_user
from ..models import Alert
from ..response import ok, fail, page_data

router = APIRouter(prefix="/alert", tags=["告警中心"])


class HandleIn(BaseModel):
    status: str  # processing/resolved/false
    handle_remark: str | None = None


@router.get("/page")
def list_alerts(page: int = 1, pageSize: int = 10, keyword: str | None = None,
                severity: str | None = None, status: str | None = None,
                alert_type: str | None = None,
                db: Session = Depends(get_db), current=Depends(get_current_user)):
    q = db.query(Alert)
    if keyword:
        q = q.filter(Alert.title.like(f"%{keyword}%"))
    if severity:
        q = q.filter(Alert.severity == severity)
    if status:
        q = q.filter(Alert.status == status)
    if alert_type:
        q = q.filter(Alert.alert_type == alert_type)
    total = q.count()
    rows = q.order_by(Alert.id.desc()).offset((page - 1) * pageSize).limit(pageSize).all()
    return ok(page_data([{
        "id": a.id, "title": a.title, "alert_type": a.alert_type,
        "severity": a.severity, "source": a.source, "description": a.description,
        "status": a.status, "handler": a.handler, "handle_remark": a.handle_remark,
        "handle_time": a.handle_time, "create_time": a.create_time,
    } for a in rows], total, page, pageSize))


@router.put("/handle/{aid}")
def handle(aid: int, body: HandleIn, db: Session = Depends(get_db), current=Depends(get_current_user)):
    a = db.query(Alert).get(aid)
    if not a:
        return fail("告警不存在")
    a.status = body.status
    a.handle_remark = body.handle_remark
    a.handler = current.username
    a.handle_time = datetime.now()
    db.commit()
    return ok(msg="处理成功")


@router.delete("/delete/{aid}")
def delete_alert(aid: int, db: Session = Depends(get_db), current=Depends(get_current_user)):
    a = db.query(Alert).get(aid)
    if not a:
        return fail("告警不存在")
    db.delete(a)
    db.commit()
    return ok(msg="删除成功")
