"""漏洞-修复方案库"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import get_current_user
from ..models import VulnFixMapping
from ..response import ok, fail, page_data

router = APIRouter(prefix="/vuln-fix", tags=["漏洞修复库"])


class VulnFixIn(BaseModel):
    vuln_type: str
    severity: str = "medium"
    description: str | None = None
    fix_advice: str | None = None
    patch_url: str | None = None
    reference: str | None = None


@router.get("/page")
def list_vf(page: int = 1, pageSize: int = 10, keyword: str | None = None,
            severity: str | None = None,
            db: Session = Depends(get_db), current=Depends(get_current_user)):
    q = db.query(VulnFixMapping)
    if keyword:
        q = q.filter(VulnFixMapping.vuln_type.like(f"%{keyword}%"))
    if severity:
        q = q.filter(VulnFixMapping.severity == severity)
    total = q.count()
    rows = q.order_by(VulnFixMapping.id.desc()).offset((page - 1) * pageSize).limit(pageSize).all()
    return ok(page_data([{
        "id": r.id, "vuln_type": r.vuln_type, "severity": r.severity,
        "description": r.description, "fix_advice": r.fix_advice,
        "patch_url": r.patch_url, "reference": r.reference,
        "create_time": r.create_time, "update_time": r.update_time,
    } for r in rows], total, page, pageSize))


@router.post("/add")
def add_vf(body: VulnFixIn, db: Session = Depends(get_db), current=Depends(get_current_user)):
    if db.query(VulnFixMapping).filter(VulnFixMapping.vuln_type == body.vuln_type).first():
        return fail("该漏洞类型已存在")
    r = VulnFixMapping(**body.model_dump())
    db.add(r)
    db.commit()
    return ok({"id": r.id})


@router.put("/update/{rid}")
def update_vf(rid: int, body: VulnFixIn, db: Session = Depends(get_db), current=Depends(get_current_user)):
    r = db.query(VulnFixMapping).get(rid)
    if not r:
        return fail("不存在")
    for k, v in body.model_dump().items():
        setattr(r, k, v)
    db.commit()
    return ok(msg="修改成功")


@router.delete("/delete/{rid}")
def del_vf(rid: int, db: Session = Depends(get_db), current=Depends(get_current_user)):
    r = db.query(VulnFixMapping).get(rid)
    if not r:
        return fail("不存在")
    db.delete(r)
    db.commit()
    return ok(msg="删除成功")
