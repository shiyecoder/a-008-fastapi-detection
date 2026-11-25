"""恶意文件哈希黑名单库管理"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import get_current_user
from ..models import HashBlacklist
from ..response import ok, fail, page_data
import re

router = APIRouter(prefix="/hash-lib", tags=["哈希黑名单"])

SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


class HashIn(BaseModel):
    file_hash: str
    label: str | None = None
    severity: str | None = "high"
    description: str | None = None
    source: str | None = None
    enabled: int = 1


@router.get("/page")
def list_hash(page: int = 1, pageSize: int = 10, keyword: str | None = None,
              severity: str | None = None, enabled: int | None = None,
              db: Session = Depends(get_db), current=Depends(get_current_user)):
    q = db.query(HashBlacklist)
    if keyword:
        q = q.filter((HashBlacklist.file_hash.like(f"%{keyword}%")) | (HashBlacklist.label.like(f"%{keyword}%")))
    if severity:
        q = q.filter(HashBlacklist.severity == severity)
    if enabled is not None:
        q = q.filter(HashBlacklist.enabled == enabled)
    total = q.count()
    rows = q.order_by(HashBlacklist.id.desc()).offset((page - 1) * pageSize).limit(pageSize).all()
    return ok(page_data([{
        "id": r.id, "file_hash": r.file_hash, "label": r.label,
        "severity": r.severity, "description": r.description,
        "source": r.source, "enabled": r.enabled, "create_time": r.create_time,
    } for r in rows], total, page, pageSize))


@router.post("/add")
def add_hash(body: HashIn, db: Session = Depends(get_db), current=Depends(get_current_user)):
    h = body.file_hash.strip().lower()
    if not SHA256_RE.match(h):
        return fail("哈希格式非法（必须是 64 位 SHA256 十六进制）")
    if db.query(HashBlacklist).filter(HashBlacklist.file_hash == h).first():
        return fail("该哈希已存在")
    data = body.model_dump(); data["file_hash"] = h
    r = HashBlacklist(**data)
    db.add(r); db.commit()
    return ok({"id": r.id})


@router.put("/update/{rid}")
def update_hash(rid: int, body: HashIn, db: Session = Depends(get_db), current=Depends(get_current_user)):
    r = db.query(HashBlacklist).get(rid)
    if not r:
        return fail("记录不存在")
    h = body.file_hash.strip().lower()
    if not SHA256_RE.match(h):
        return fail("哈希格式非法")
    data = body.model_dump(); data["file_hash"] = h
    for k, v in data.items():
        setattr(r, k, v)
    db.commit()
    return ok(msg="修改成功")


@router.delete("/delete/{rid}")
def del_hash(rid: int, db: Session = Depends(get_db), current=Depends(get_current_user)):
    r = db.query(HashBlacklist).get(rid)
    if not r:
        return fail("记录不存在")
    db.delete(r); db.commit()
    return ok(msg="删除成功")


@router.put("/toggle/{rid}")
def toggle_hash(rid: int, db: Session = Depends(get_db), current=Depends(get_current_user)):
    r = db.query(HashBlacklist).get(rid)
    if not r:
        return fail("记录不存在")
    r.enabled = 0 if r.enabled == 1 else 1
    db.commit()
    return ok(msg="状态已切换")
