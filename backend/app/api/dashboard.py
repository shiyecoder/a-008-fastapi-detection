"""仪表盘统计接口（5-7个图表）"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from ..database import get_db
from ..deps import get_current_user
from ..models import (
    DetectionTask, Alert, QuarantineFile,
    DetectionResult, SysUser
)
from ..response import ok

router = APIRouter(prefix="/dashboard", tags=["仪表盘"])


@router.get("/overview")
def overview(db: Session = Depends(get_db), current=Depends(get_current_user)):
    """顶部数据卡片"""
    return ok({
        "totalTasks": db.query(DetectionTask).count(),
        "webshellCount": db.query(DetectionTask).filter(DetectionTask.risk_level.in_(["high", "medium"])).count(),
        "alertCount": db.query(Alert).filter(Alert.status == "pending").count(),
        "quarantineCount": db.query(QuarantineFile).filter(QuarantineFile.status == "quarantined").count(),
        "userCount": db.query(SysUser).count(),
    })


@router.get("/trend")
def trend(db: Session = Depends(get_db), current=Depends(get_current_user)):
    """图表1：近30天检测任务趋势"""
    today = datetime.now().date()
    start = today - timedelta(days=29)
    rows = db.query(
        func.date(DetectionTask.create_time).label("d"),
        func.count(DetectionTask.id).label("cnt")
    ).filter(DetectionTask.create_time >= start).group_by("d").all()
    daily = {r.d.strftime("%Y-%m-%d") if hasattr(r.d, "strftime") else str(r.d): r.cnt for r in rows}
    dates = []
    counts = []
    for i in range(30):
        d = (start + timedelta(days=i)).strftime("%Y-%m-%d")
        dates.append(d)
        counts.append(daily.get(d, 0))
    return ok({"dates": dates, "counts": counts})


@router.get("/lang-distribution")
def lang_distribution(db: Session = Depends(get_db), current=Depends(get_current_user)):
    """图表2：检出语言分布饼图"""
    rows = db.query(DetectionTask.language, func.count(DetectionTask.id)).filter(
        DetectionTask.risk_level.in_(["high", "medium"])
    ).group_by(DetectionTask.language).all()
    return ok([{"name": (r[0] or "未知").upper(), "value": r[1]} for r in rows])


@router.get("/detect-type")
def detect_type(db: Session = Depends(get_db), current=Depends(get_current_user)):
    """图表3：检测方式占比"""
    rows = db.query(DetectionTask.detect_type, func.count(DetectionTask.id)).group_by(DetectionTask.detect_type).all()
    name_map = {"static": "静态检测", "dynamic": "动态检测", "mixed": "混合检测"}
    return ok([{"name": name_map.get(r[0], r[0] or "其他"), "value": r[1]} for r in rows])


@router.get("/risk-level")
def risk_level(db: Session = Depends(get_db), current=Depends(get_current_user)):
    """图表4：风险等级分布"""
    rows = db.query(DetectionTask.risk_level, func.count(DetectionTask.id)).group_by(DetectionTask.risk_level).all()
    name_map = {"high": "高危", "medium": "中危", "low": "低危", "safe": "安全"}
    data = {name_map.get(r[0], r[0] or "未知"): r[1] for r in rows}
    return ok({
        "levels": ["高危", "中危", "低危", "安全"],
        "counts": [data.get("高危", 0), data.get("中危", 0), data.get("低危", 0), data.get("安全", 0)],
    })


@router.get("/alert-status")
def alert_status(db: Session = Depends(get_db), current=Depends(get_current_user)):
    """图表5：告警处理状态"""
    rows = db.query(Alert.status, func.count(Alert.id)).group_by(Alert.status).all()
    name_map = {"pending": "未处理", "processing": "处理中", "resolved": "已处理", "false": "误报"}
    return ok([{"name": name_map.get(r[0], r[0] or "其他"), "value": r[1]} for r in rows])


@router.get("/recent-alerts")
def recent_alerts(limit: int = 8, db: Session = Depends(get_db), current=Depends(get_current_user)):
    """最近告警 (安全管理员/admin 用)"""
    rows = db.query(Alert).order_by(Alert.id.desc()).limit(limit).all()
    return ok([{
        "id": r.id, "title": r.title, "severity": r.severity,
        "status": r.status, "create_time": r.create_time
    } for r in rows])


@router.get("/recent-quarantine")
def recent_quarantine(limit: int = 8, db: Session = Depends(get_db), current=Depends(get_current_user)):
    """最近隔离文件"""
    rows = db.query(QuarantineFile).order_by(QuarantineFile.id.desc()).limit(limit).all()
    return ok([{
        "id": r.id, "file_name": r.file_name, "risk_level": r.risk_level,
        "status": r.status, "hit_rule": r.hit_rule, "create_time": r.create_time
    } for r in rows])


@router.get("/my-stats")
def my_stats(db: Session = Depends(get_db), current=Depends(get_current_user)):
    """普通用户：我的统计"""
    uid = current.id
    my_tasks = db.query(DetectionTask).filter(DetectionTask.user_id == uid).count()
    my_high = db.query(DetectionTask).filter(
        DetectionTask.user_id == uid,
        DetectionTask.risk_level.in_(["high", "medium"])
    ).count()
    my_safe = db.query(DetectionTask).filter(
        DetectionTask.user_id == uid,
        DetectionTask.risk_level.in_(["low", "safe"])
    ).count()
    # 我的最近 8 条检测任务
    recent = db.query(DetectionTask).filter(DetectionTask.user_id == uid).order_by(
        DetectionTask.id.desc()
    ).limit(8).all()
    return ok({
        "myTasks": my_tasks,
        "myHigh": my_high,
        "mySafe": my_safe,
        "recent": [{
            "id": r.id, "file_name": r.file_name, "risk_level": r.risk_level,
            "detect_type": r.detect_type, "create_time": r.create_time
        } for r in recent]
    })


@router.get("/my-trend")
def my_trend(db: Session = Depends(get_db), current=Depends(get_current_user)):
    """普通用户：我的近 14 天检测趋势"""
    today = datetime.now().date()
    start = today - timedelta(days=13)
    rows = db.query(
        func.date(DetectionTask.create_time).label("d"),
        func.count(DetectionTask.id).label("cnt")
    ).filter(
        DetectionTask.user_id == current.id,
        DetectionTask.create_time >= start
    ).group_by("d").all()
    daily = {r.d.strftime("%Y-%m-%d") if hasattr(r.d, "strftime") else str(r.d): r.cnt for r in rows}
    dates, counts = [], []
    for i in range(14):
        d = (start + timedelta(days=i)).strftime("%Y-%m-%d")
        dates.append(d[5:])
        counts.append(daily.get(d, 0))
    return ok({"dates": dates, "counts": counts})

