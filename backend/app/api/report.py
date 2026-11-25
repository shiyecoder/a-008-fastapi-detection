"""报告中心：综合报告生成"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
import json
from ..database import get_db
from ..deps import get_current_user
from ..models import (
    Report, DetectionTask, DetectionResult
)
from ..response import ok, fail, page_data

router = APIRouter(prefix="/report", tags=["报告中心"])


class ReportIn(BaseModel):
    title: str
    report_type: str  # static / dynamic / comprehensive
    related_task_id: int | None = None


@router.get("/page")
def list_reports(page: int = 1, pageSize: int = 10, keyword: str | None = None,
                 report_type: str | None = None,
                 db: Session = Depends(get_db), current=Depends(get_current_user)):
    q = db.query(Report)
    if keyword:
        q = q.filter(Report.title.like(f"%{keyword}%"))
    if report_type:
        q = q.filter(Report.report_type == report_type)
    total = q.count()
    rows = q.order_by(Report.id.desc()).offset((page - 1) * pageSize).limit(pageSize).all()
    return ok(page_data([{
        "id": r.id, "title": r.title, "report_type": r.report_type,
        "related_task_id": r.related_task_id, "risk_level": r.risk_level,
        "create_time": r.create_time,
    } for r in rows], total, page, pageSize))


@router.post("/generate")
def generate(body: ReportIn, db: Session = Depends(get_db), current=Depends(get_current_user)):
    """生成报告"""
    content = {"sections": []}
    risk = "safe"

    if body.report_type == "comprehensive":
        # 综合：取最近若干任务汇总
        det = db.query(DetectionTask).order_by(DetectionTask.id.desc()).limit(20).all()
        content["sections"].append({
            "title": "Webshell检测概览",
            "items": [{"id": t.id, "name": t.task_name, "risk": t.risk_level, "hits": t.hit_count} for t in det]
        })
        risks = [x.risk_level for x in det if x.risk_level]
        risk = "high" if "high" in risks else "medium" if "medium" in risks else "low"
    elif body.report_type in ("static", "dynamic") and body.related_task_id:
        t = db.query(DetectionTask).get(body.related_task_id)
        if not t:
            return fail("任务不存在")
        fs = db.query(DetectionResult).filter(DetectionResult.task_id == t.id).all()
        content["task"] = {"id": t.id, "name": t.task_name, "file": t.file_name}
        content["findings"] = [{
            "rule": f.rule_name, "severity": f.severity, "line": f.line_no,
            "snippet": f.code_snippet, "desc": f.description, "fix": f.fix_advice
        } for f in fs]
        risk = t.risk_level or "safe"

    rep = Report(
        title=body.title, report_type=body.report_type,
        related_task_id=body.related_task_id, risk_level=risk,
        content=json.dumps(content, ensure_ascii=False),
        user_id=current.id,
    )
    db.add(rep)
    db.commit()
    return ok({"id": rep.id})


@router.get("/detail/{rid}")
def detail(rid: int, db: Session = Depends(get_db), current=Depends(get_current_user)):
    r = db.query(Report).get(rid)
    if not r:
        return fail("报告不存在")
    try:
        content = json.loads(r.content) if r.content else {}
    except Exception:
        content = {}
    return ok({
        "id": r.id, "title": r.title, "report_type": r.report_type,
        "related_task_id": r.related_task_id, "risk_level": r.risk_level,
        "content": content, "create_time": r.create_time,
    })


@router.delete("/delete/{rid}")
def del_report(rid: int, db: Session = Depends(get_db), current=Depends(get_current_user)):
    r = db.query(Report).get(rid)
    if not r:
        return fail("不存在")
    db.delete(r)
    db.commit()
    return ok(msg="删除成功")
