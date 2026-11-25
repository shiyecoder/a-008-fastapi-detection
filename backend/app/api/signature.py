"""静态签名规则库管理"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import get_current_user
from ..models import SignatureRule
from ..response import ok, fail, page_data
import re

router = APIRouter(prefix="/signature", tags=["签名规则库"])


class SignatureIn(BaseModel):
    rule_name: str
    language: str | None = "any"
    severity: str | None = "medium"
    pattern: str
    description: str | None = None
    fix_advice: str | None = None
    enabled: int = 1


def _validate(pattern: str) -> str | None:
    try:
        re.compile(pattern)
        return None
    except re.error as e:
        return f"正则非法：{e}"


@router.get("/page")
def list_rules(page: int = 1, pageSize: int = 10, keyword: str | None = None,
               language: str | None = None, enabled: int | None = None,
               db: Session = Depends(get_db), current=Depends(get_current_user)):
    q = db.query(SignatureRule)
    if keyword:
        q = q.filter(SignatureRule.rule_name.like(f"%{keyword}%"))
    if language:
        q = q.filter(SignatureRule.language == language)
    if enabled is not None:
        q = q.filter(SignatureRule.enabled == enabled)
    total = q.count()
    rows = q.order_by(SignatureRule.id.desc()).offset((page - 1) * pageSize).limit(pageSize).all()
    return ok(page_data([{
        "id": r.id, "rule_name": r.rule_name, "language": r.language,
        "severity": r.severity, "pattern": r.pattern, "description": r.description,
        "fix_advice": r.fix_advice, "enabled": r.enabled,
        "create_time": r.create_time, "update_time": r.update_time,
    } for r in rows], total, page, pageSize))


@router.post("/add")
def add_rule(body: SignatureIn, db: Session = Depends(get_db), current=Depends(get_current_user)):
    err = _validate(body.pattern)
    if err:
        return fail(err)
    if db.query(SignatureRule).filter(SignatureRule.rule_name == body.rule_name).first():
        return fail("规则名已存在")
    r = SignatureRule(**body.model_dump())
    db.add(r); db.commit()
    return ok({"id": r.id})


@router.put("/update/{rid}")
def update_rule(rid: int, body: SignatureIn, db: Session = Depends(get_db), current=Depends(get_current_user)):
    r = db.query(SignatureRule).get(rid)
    if not r:
        return fail("规则不存在")
    err = _validate(body.pattern)
    if err:
        return fail(err)
    for k, v in body.model_dump().items():
        setattr(r, k, v)
    db.commit()
    return ok(msg="修改成功")


@router.delete("/delete/{rid}")
def del_rule(rid: int, db: Session = Depends(get_db), current=Depends(get_current_user)):
    r = db.query(SignatureRule).get(rid)
    if not r:
        return fail("规则不存在")
    db.delete(r); db.commit()
    return ok(msg="删除成功")


@router.put("/toggle/{rid}")
def toggle_rule(rid: int, db: Session = Depends(get_db), current=Depends(get_current_user)):
    r = db.query(SignatureRule).get(rid)
    if not r:
        return fail("规则不存在")
    r.enabled = 0 if r.enabled == 1 else 1
    db.commit()
    return ok(msg="状态已切换")
