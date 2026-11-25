"""检测任务：静态/动态/混合 + 检测结果 + 文件上传"""
from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from datetime import datetime
from ..database import get_db
from ..deps import get_current_user
from ..models import DetectionTask, DetectionResult, YaraRule, Alert, QuarantineFile, VulnFixMapping, SignatureRule, HashBlacklist
from ..response import ok, fail, page_data
from ..config import settings
from ..upload_util import save_upload_file, abs_path_of
from ..detection_engine import (
    static_scan, dynamic_scan, detect_language_by_ext, file_sha256, resolve_language
)
import os
import shutil

router = APIRouter(prefix="/detection", tags=["检测任务"])


def _load_user_yara_rules(db: Session):
    rules = db.query(YaraRule).filter(YaraRule.enabled == 1).all()
    return [{
        "name": r.rule_name, "lang": r.language or "any",
        "severity": r.severity or "medium", "pattern": r.pattern or "",
        "description": r.description or "", "fix_advice": "",
    } for r in rules]


def _load_user_signatures(db: Session):
    rows = db.query(SignatureRule).filter(SignatureRule.enabled == 1).all()
    return [{
        "name": r.rule_name, "lang": r.language or "any",
        "severity": r.severity or "medium", "pattern": r.pattern or "",
        "desc": r.description or "", "fix": r.fix_advice or "",
    } for r in rows]


def _load_user_bad_hashes(db: Session):
    rows = db.query(HashBlacklist).filter(HashBlacklist.enabled == 1).all()
    return {r.file_hash: (r.label or "BadHash") for r in rows}


@router.post("/scan")
def create_scan(
    task_name: str = Form(...),
    detect_type: str = Form("static"),  # static / dynamic / mixed
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    """上传文件并立即执行检测"""
    info = save_upload_file(file, settings.DETECTION_DIR)
    language = resolve_language(info["abs_path"], info["file_name"])
    sha = file_sha256(info["abs_path"])

    task = DetectionTask(
        task_name=task_name,
        detect_type=detect_type,
        target_type="file",
        file_path=info["rel_path"],
        file_name=info["file_name"],
        file_size=info["size"],
        file_hash=sha,
        language=language,
        status="running",
        user_id=current.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    findings = []
    if detect_type in ("static", "mixed"):
        r1 = static_scan(
            info["abs_path"], language,
            extra_yara_rules=_load_user_yara_rules(db),
            extra_signatures=_load_user_signatures(db),
            extra_bad_hashes=_load_user_bad_hashes(db),
        )
        findings.extend(r1["findings"])
    if detect_type in ("dynamic", "mixed"):
        r2 = dynamic_scan(info["abs_path"], language)
        findings.extend(r2["findings"])

    # 计算风险等级
    sev = [f["severity"] for f in findings]
    if "high" in sev:
        risk = "high"
    elif "medium" in sev:
        risk = "medium"
    elif "low" in sev:
        risk = "low"
    else:
        risk = "safe"

    task.risk_level = risk
    task.hit_count = len(findings)
    task.status = "finished"
    task.finish_time = datetime.now()
    task.summary = f"共命中{len(findings)}条规则，最高风险等级：{risk}"
    db.commit()

    # 写入结果详情
    for f in findings:
        db.add(DetectionResult(task_id=task.id, **f))

    # 高/中风险产生告警
    if risk in ("high", "medium"):
        db.add(Alert(
            title=f"检出可疑Webshell：{info['file_name']}",
            alert_type="webshell",
            severity=risk,
            source=f"任务#{task.id}",
            description=task.summary,
            status="pending",
        ))
    db.commit()
    # 风险分：高100 / 中60 / 低30 / 安全0，叠加命中数微调
    score_base = {"high": 100, "medium": 60, "low": 30, "safe": 0}[risk]
    score = min(100, score_base + max(0, len(findings) - 1) * 2)
    return ok({
        "task_id": task.id,
        "file_name": task.file_name,
        "file_size": task.file_size,
        "language": task.language,
        "risk_level": risk,
        "hit_count": len(findings),
        "score": score,
        "summary": task.summary,
    })


@router.get("/page")
def list_tasks(
    page: int = 1, pageSize: int = 10,
    keyword: str | None = None,
    detect_type: str | None = None,
    risk_level: str | None = None,
    db: Session = Depends(get_db), current=Depends(get_current_user),
):
    q = db.query(DetectionTask)
    if keyword:
        q = q.filter(DetectionTask.task_name.like(f"%{keyword}%"))
    if detect_type:
        q = q.filter(DetectionTask.detect_type == detect_type)
    if risk_level:
        q = q.filter(DetectionTask.risk_level == risk_level)
    total = q.count()
    rows = q.order_by(DetectionTask.id.desc()).offset((page - 1) * pageSize).limit(pageSize).all()
    return ok(page_data([{
        "id": t.id, "task_name": t.task_name, "detect_type": t.detect_type,
        "file_name": t.file_name, "file_size": t.file_size, "file_hash": t.file_hash,
        "language": t.language, "status": t.status,
        "risk_level": t.risk_level, "hit_count": t.hit_count,
        "summary": t.summary, "create_time": t.create_time, "finish_time": t.finish_time,
    } for t in rows], total, page, pageSize))


@router.get("/detail/{tid}")
def detail(tid: int, db: Session = Depends(get_db), current=Depends(get_current_user)):
    t = db.query(DetectionTask).get(tid)
    if not t:
        return fail("任务不存在")
    findings = db.query(DetectionResult).filter(DetectionResult.task_id == tid).all()
    # 自动关联漏洞-修复方案库（按命中规则名匹配 vuln_type 关键词）
    fix_map = {}
    if findings:
        rule_names = list({f.rule_name for f in findings})
        all_fix = db.query(VulnFixMapping).all()
        for fm in all_fix:
            for rn in rule_names:
                if fm.vuln_type and (fm.vuln_type in rn or rn.split("-")[0].lower() in fm.vuln_type.lower()):
                    fix_map.setdefault(rn, {
                        "vuln_type": fm.vuln_type,
                        "fix_advice": fm.fix_advice,
                        "patch_url": fm.patch_url,
                        "reference": fm.reference,
                    })
    return ok({
        "task": {
            "id": t.id, "task_name": t.task_name, "detect_type": t.detect_type,
            "file_name": t.file_name, "file_size": t.file_size, "file_hash": t.file_hash,
            "language": t.language, "status": t.status,
            "risk_level": t.risk_level, "hit_count": t.hit_count,
            "summary": t.summary, "create_time": t.create_time, "finish_time": t.finish_time,
        },
        "findings": [{
            "id": f.id, "rule_name": f.rule_name, "rule_type": f.rule_type,
            "severity": f.severity, "line_no": f.line_no,
            "code_snippet": f.code_snippet, "description": f.description,
            "fix_advice": f.fix_advice,
            "fix_mapping": fix_map.get(f.rule_name),
        } for f in findings],
    })


@router.get("/scope/{tid}")
def infection_scope(tid: int, db: Session = Depends(get_db), current=Depends(get_current_user)):
    """感染范围定位：列出与命中文件同目录、同哈希、或最近30分钟内提交的可疑文件"""
    t = db.query(DetectionTask).get(tid)
    if not t:
        return fail("任务不存在")
    related = []
    # 1. 同哈希文件（已知恶意复制传播）
    same_hash = db.query(DetectionTask).filter(
        DetectionTask.file_hash == t.file_hash,
        DetectionTask.id != t.id,
        DetectionTask.file_hash != None,
        DetectionTask.file_hash != "",
    ).limit(20).all()
    for s in same_hash:
        related.append({
            "id": s.id, "file_name": s.file_name, "file_path": s.file_path,
            "risk_level": s.risk_level, "match_reason": "相同文件哈希（同源传播）",
            "create_time": s.create_time,
        })
    # 2. 同目录文件
    if t.file_path:
        dir_prefix = os.path.dirname(t.file_path).replace("\\", "/")
        if dir_prefix:
            same_dir = db.query(DetectionTask).filter(
                DetectionTask.file_path.like(f"{dir_prefix}/%"),
                DetectionTask.id != t.id,
                DetectionTask.risk_level.in_(["high", "medium"]),
            ).limit(20).all()
            for s in same_dir:
                related.append({
                    "id": s.id, "file_name": s.file_name, "file_path": s.file_path,
                    "risk_level": s.risk_level, "match_reason": "同上传目录可疑文件",
                    "create_time": s.create_time,
                })
    # 3. 同用户最近30分钟内提交的高/中风险文件
    from datetime import timedelta
    recent_time = (t.create_time or datetime.now()) - timedelta(minutes=30)
    recent = db.query(DetectionTask).filter(
        DetectionTask.user_id == t.user_id,
        DetectionTask.id != t.id,
        DetectionTask.create_time >= recent_time,
        DetectionTask.risk_level.in_(["high", "medium"]),
    ).limit(20).all()
    for s in recent:
        related.append({
            "id": s.id, "file_name": s.file_name, "file_path": s.file_path,
            "risk_level": s.risk_level, "match_reason": "同操作者短时间内提交",
            "create_time": s.create_time,
        })
    # 去重
    seen = set()
    unique = []
    for r in related:
        if r["id"] in seen:
            continue
        seen.add(r["id"])
        unique.append(r)
    return ok({
        "origin": {"id": t.id, "file_name": t.file_name, "file_hash": t.file_hash},
        "scope_count": len(unique),
        "related_files": unique,
    })


@router.delete("/delete/{tid}")
def delete_task(tid: int, db: Session = Depends(get_db), current=Depends(get_current_user)):
    t = db.query(DetectionTask).get(tid)
    if not t:
        return fail("任务不存在")
    db.query(DetectionResult).filter(DetectionResult.task_id == tid).delete()
    db.delete(t)
    db.commit()
    return ok(msg="删除成功")


@router.post("/quarantine/{tid}")
def quarantine_task(tid: int, db: Session = Depends(get_db), current=Depends(get_current_user)):
    """将检测任务对应的文件隔离"""
    t = db.query(DetectionTask).get(tid)
    if not t:
        return fail("任务不存在")
    if not t.file_path:
        return fail("无关联文件")
    src = abs_path_of(t.file_path)
    if not os.path.exists(src):
        return fail("文件已不存在")
    qdir = os.path.join(settings.UPLOAD_ROOT, settings.QUARANTINE_DIR, datetime.now().strftime("%Y%m"))
    os.makedirs(qdir, exist_ok=True)
    qname = f"q_{t.id}_{t.file_name}"
    qpath = os.path.join(qdir, qname)
    shutil.copy2(src, qpath)
    rel_q = f"{settings.QUARANTINE_DIR}/{datetime.now().strftime('%Y%m')}/{qname}".replace("\\", "/")
    db.add(QuarantineFile(
        file_name=t.file_name, origin_path=t.file_path,
        quarantine_path=rel_q, file_hash=t.file_hash, file_size=t.file_size,
        hit_rule=str(t.hit_count) + "条规则",
        risk_level=t.risk_level, status="quarantined",
        task_id=t.id, user_id=current.id,
    ))
    db.commit()
    return ok(msg="已隔离")
