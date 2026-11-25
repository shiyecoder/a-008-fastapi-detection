"""ORM 模型：所有数据表"""
from sqlalchemy import (
    Column, Integer, String, DateTime, Text, BigInteger, ForeignKey, Boolean, SmallInteger
)
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


# ========== 系统用户/角色/菜单 ==========

class SysUser(Base):
    __tablename__ = "sys_user"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, comment="用户名")
    password = Column(String(255), nullable=False, comment="加密密码")
    nickname = Column(String(64), comment="昵称")
    email = Column(String(128), comment="邮箱")
    phone = Column(String(32), comment="手机")
    avatar = Column(String(255), comment="头像相对路径")
    status = Column(SmallInteger, default=1, comment="1启用 0禁用")
    remark = Column(String(255), comment="备注")
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class SysRole(Base):
    __tablename__ = "sys_role"
    id = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String(64), nullable=False, comment="角色名")
    role_code = Column(String(64), unique=True, nullable=False, comment="角色编码")
    status = Column(SmallInteger, default=1)
    remark = Column(String(255))
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class SysMenu(Base):
    __tablename__ = "sys_menu"
    id = Column(Integer, primary_key=True, autoincrement=True)
    parent_id = Column(Integer, default=0, comment="父菜单ID 0为顶级")
    name = Column(String(64), nullable=False, comment="菜单名称")
    path = Column(String(128), comment="路由path")
    component = Column(String(128), comment="vue组件路径")
    icon = Column(String(64), comment="图标")
    sort = Column(Integer, default=0)
    menu_type = Column(SmallInteger, default=1, comment="1菜单 2按钮")
    perms = Column(String(128), comment="权限标识")
    visible = Column(SmallInteger, default=1, comment="1显示 0隐藏")
    create_time = Column(DateTime, default=datetime.now)


class SysUserRole(Base):
    __tablename__ = "sys_user_role"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    role_id = Column(Integer, nullable=False)


class SysRoleMenu(Base):
    __tablename__ = "sys_role_menu"
    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, nullable=False)
    menu_id = Column(Integer, nullable=False)


class SysLog(Base):
    __tablename__ = "sys_log"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer)
    username = Column(String(64))
    module = Column(String(64), comment="模块")
    operation = Column(String(128), comment="操作")
    method = Column(String(8))
    url = Column(String(255))
    ip = Column(String(64))
    status = Column(SmallInteger, default=1, comment="1成功 0失败")
    create_time = Column(DateTime, default=datetime.now)


# ========== 业务表 ==========

class DetectionTask(Base):
    """检测任务（静态/动态）"""
    __tablename__ = "detection_task"
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_name = Column(String(128), nullable=False, comment="任务名称")
    detect_type = Column(String(16), comment="static/dynamic/mixed")
    target_type = Column(String(16), comment="file/dir")
    file_path = Column(String(255), comment="上传文件相对路径")
    file_name = Column(String(255))
    file_size = Column(BigInteger, default=0)
    file_hash = Column(String(64), comment="SHA256")
    language = Column(String(16), comment="php/jsp/asp/python")
    status = Column(String(16), default="pending", comment="pending/running/finished/failed")
    risk_level = Column(String(16), comment="high/medium/low/safe")
    hit_count = Column(Integer, default=0, comment="命中规则数")
    summary = Column(Text, comment="结果摘要")
    user_id = Column(Integer)
    create_time = Column(DateTime, default=datetime.now)
    finish_time = Column(DateTime)


class DetectionResult(Base):
    """单次命中详情"""
    __tablename__ = "detection_result"
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, nullable=False)
    rule_name = Column(String(128), comment="命中规则")
    rule_type = Column(String(32), comment="signature/yara/hash/behavior")
    severity = Column(String(16), comment="high/medium/low")
    line_no = Column(Integer)
    code_snippet = Column(Text, comment="代码片段")
    description = Column(Text)
    fix_advice = Column(Text)
    create_time = Column(DateTime, default=datetime.now)


class YaraRule(Base):
    __tablename__ = "yara_rule"
    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_name = Column(String(128), unique=True, nullable=False)
    language = Column(String(16), comment="适用语言")
    severity = Column(String(16), default="medium")
    pattern = Column(Text, comment="规则正则/特征")
    description = Column(Text)
    enabled = Column(SmallInteger, default=1)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class SignatureRule(Base):
    """静态签名规则库（可前端管理）"""
    __tablename__ = "signature_rule"
    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_name = Column(String(128), unique=True, nullable=False)
    language = Column(String(16), default="any", comment="any/php/jsp/asp/python")
    severity = Column(String(16), default="medium")
    pattern = Column(Text, comment="正则签名")
    description = Column(Text)
    fix_advice = Column(Text)
    enabled = Column(SmallInteger, default=1)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class HashBlacklist(Base):
    """恶意文件哈希黑名单库（可前端管理）"""
    __tablename__ = "hash_blacklist"
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_hash = Column(String(64), unique=True, nullable=False, comment="SHA256")
    label = Column(String(128), comment="家族/标签")
    severity = Column(String(16), default="high")
    description = Column(Text)
    source = Column(String(128), comment="来源")
    enabled = Column(SmallInteger, default=1)
    create_time = Column(DateTime, default=datetime.now)



class QuarantineFile(Base):
    __tablename__ = "quarantine_file"
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_name = Column(String(255))
    origin_path = Column(String(512), comment="原路径")
    quarantine_path = Column(String(512), comment="隔离路径")
    file_hash = Column(String(64))
    file_size = Column(BigInteger, default=0)
    hit_rule = Column(String(128))
    risk_level = Column(String(16))
    status = Column(String(16), default="quarantined", comment="quarantined/restored/deleted")
    task_id = Column(Integer)
    user_id = Column(Integer)
    create_time = Column(DateTime, default=datetime.now)


class Alert(Base):
    __tablename__ = "alert"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    alert_type = Column(String(32), comment="webshell/intrusion")
    severity = Column(String(16), default="medium")
    source = Column(String(128), comment="来源任务/IP")
    description = Column(Text)
    status = Column(String(16), default="pending", comment="pending/processing/resolved/false")
    handler = Column(String(64))
    handle_remark = Column(Text)
    handle_time = Column(DateTime)
    create_time = Column(DateTime, default=datetime.now)


class VulnFixMapping(Base):
    """漏洞-修复方案库"""
    __tablename__ = "vuln_fix_mapping"
    id = Column(Integer, primary_key=True, autoincrement=True)
    vuln_type = Column(String(64), unique=True, nullable=False)
    severity = Column(String(16), default="medium")
    description = Column(Text)
    fix_advice = Column(Text, comment="修复建议")
    patch_url = Column(String(255), comment="补丁链接")
    reference = Column(String(255))
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Report(Base):
    __tablename__ = "report"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    report_type = Column(String(32), comment="static/dynamic/comprehensive")
    related_task_id = Column(Integer)
    risk_level = Column(String(16))
    content = Column(Text, comment="报告内容（JSON或HTML）")
    user_id = Column(Integer)
    create_time = Column(DateTime, default=datetime.now)
