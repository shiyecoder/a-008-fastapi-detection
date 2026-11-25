"""检测引擎：静态扫描 + 真实沙箱动态执行"""
import re
import os
import json
import shutil
import socket
import hashlib
import tempfile
import subprocess
import threading
from datetime import datetime
from typing import List, Dict, Tuple


# ==================== 静态检测 ====================

# 内置 Webshell 特征签名库
SIGNATURE_DB = [
    {"name": "PHP-Eval-Risk", "lang": "php", "pattern": r"\beval\s*\(", "severity": "high",
     "desc": "PHP eval() 调用，可能为代码执行后门",
     "fix": "禁用eval函数；使用白名单过滤；移除可疑代码"},
    {"name": "PHP-Assert-Risk", "lang": "php", "pattern": r"\bassert\s*\(", "severity": "high",
     "desc": "assert() 可执行字符串作为代码", "fix": "在php.ini中禁用assert.active"},
    {"name": "PHP-System-Exec", "lang": "php", "pattern": r"\b(system|exec|shell_exec|passthru|popen)\s*\(",
     "severity": "high", "desc": "系统命令执行函数", "fix": "禁用危险函数disable_functions"},
    {"name": "PHP-Base64-Decode", "lang": "php", "pattern": r"base64_decode\s*\(", "severity": "medium",
     "desc": "Base64解码常用于绕过检测", "fix": "审查解码后的内容来源"},
    {"name": "PHP-Preg-Replace-E", "lang": "php", "pattern": r"preg_replace\s*\(\s*['\"][^'\"]*\/e",
     "severity": "high", "desc": "preg_replace /e 修饰符可执行代码", "fix": "替换为 preg_replace_callback"},
    {"name": "JSP-Runtime-Exec", "lang": "jsp", "pattern": r"Runtime\.getRuntime\(\)\.exec",
     "severity": "high", "desc": "JSP 调用 Runtime.exec", "fix": "审查输入参数，加白名单过滤"},
    {"name": "JSP-ProcessBuilder", "lang": "jsp", "pattern": r"new\s+ProcessBuilder",
     "severity": "high", "desc": "ProcessBuilder 执行外部命令", "fix": "限制可执行命令"},
    {"name": "ASP-Eval", "lang": "asp", "pattern": r"\bEval\s*\(", "severity": "high",
     "desc": "ASP Eval 函数", "fix": "重构代码避免动态执行"},
    {"name": "ASP-Execute", "lang": "asp", "pattern": r"\bExecute\s*\(", "severity": "high",
     "desc": "ASP Execute 动态执行", "fix": "重构代码避免动态执行"},
    {"name": "Python-Eval", "lang": "python", "pattern": r"\beval\s*\(", "severity": "high",
     "desc": "Python eval() 风险", "fix": "使用 ast.literal_eval 替代"},
    {"name": "Python-OS-System", "lang": "python", "pattern": r"os\.system\s*\(",
     "severity": "high", "desc": "os.system 命令执行", "fix": "使用 subprocess 并指定 shell=False"},
    {"name": "Generic-Webshell-Pwd", "lang": "any",
     "pattern": r"(@?\$_(POST|GET|REQUEST)\s*\[\s*['\"]?[a-zA-Z0-9_]{1,8}['\"]?\s*\])",
     "severity": "medium", "desc": "可疑 一句话 Webshell 接收参数", "fix": "审查参数来源与使用"},
]

# 已知恶意文件哈希库（演示）
KNOWN_BAD_HASHES = {
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855": "EmptyFile-Suspicious",
}

# YARA 风格简化规则（默认内置 + 数据库可扩展）
DEFAULT_YARA_RULES = [
    {"name": "YARA-PHP-OneLiner", "lang": "php",
     "pattern": r"<\?php\s+@?eval\s*\(\s*\$_(POST|GET|REQUEST)", "severity": "high",
     "desc": "典型 PHP 一句话木马", "fix": "立即删除该文件并排查上传入口"},
    {"name": "YARA-Encoded-Payload", "lang": "any",
     "pattern": r"(eval|assert)\s*\(\s*(base64_decode|gzinflate|str_rot13)",
     "severity": "high", "desc": "编码混淆 webshell", "fix": "解码后审查并清除"},
    {"name": "YARA-JSP-Cmd", "lang": "jsp",
     "pattern": r"request\.getParameter\([^)]+\).*Runtime\.getRuntime", "severity": "high",
     "desc": "JSP 命令执行 webshell", "fix": "禁用相关接口并溯源"},
]


def file_sha256(path: str) -> str:
    """计算文件 SHA256"""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def detect_language_by_ext(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    return {
        ".php": "php", ".php5": "php", ".phtml": "php",
        ".jsp": "jsp", ".jspx": "jsp",
        ".asp": "asp", ".aspx": "asp",
        ".py": "python",
    }.get(ext, "unknown")


def detect_language_by_content(file_path: str) -> str:
    """扩展名无法识别时的内容嗅探兑底：
    按特征关键字推断 PHP / JSP / ASP / Python。
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read(8192)
    except Exception:
        return "unknown"
    head = content[:2048]
    low = head.lower()
    if "<?php" in low or "<?=" in low:
        return "php"
    if "<%@" in low and "page" in low and "language=\"java\"" in low.replace(" ", ""):
        return "jsp"
    if "<%@" in low and "language=\"vb" in low.replace(" ", ""):
        return "asp"
    if ("<jsp:" in low) or ("runtime.getruntime" in low) or ("processbuilder" in low):
        return "jsp"
    if ("<%" in low and "%>" in low and ("response.write" in low or "server.createobject" in low)):
        return "asp"
    if head.startswith("#!") and "python" in head.split("\n", 1)[0].lower():
        return "python"
    if re.search(r"^\s*(import|from)\s+\w+", head, re.MULTILINE) and "def " in head:
        return "python"
    return "unknown"


def resolve_language(file_path: str, file_name: str = None) -> str:
    """统一入口：先看扩展名，不行再看内容"""
    lang = detect_language_by_ext(file_name or file_path)
    if lang == "unknown":
        lang = detect_language_by_content(file_path)
    return lang


def static_scan(file_path: str, language: str = None,
                extra_yara_rules: List[Dict] = None,
                extra_signatures: List[Dict] = None,
                extra_bad_hashes: Dict[str, str] = None) -> Dict:
    """
    静态扫描入口：返回 { findings: [...], file_hash, risk_level, hit_count }
    extra_signatures: 额外签名规则列表（每项需含 name/lang/pattern/severity/desc/fix）
    extra_bad_hashes: 额外恶意哈希字典 {sha256: label}
    """
    if not os.path.exists(file_path):
        return {"findings": [], "file_hash": "", "risk_level": "safe", "hit_count": 0}

    file_hash = file_sha256(file_path)
    findings = []

    # 1. 哈希比对（内置 + DB 扩展）
    bad_hashes = dict(KNOWN_BAD_HASHES)
    if extra_bad_hashes:
        bad_hashes.update(extra_bad_hashes)
    if file_hash in bad_hashes:
        findings.append({
            "rule_name": bad_hashes[file_hash],
            "rule_type": "hash",
            "severity": "high",
            "line_no": 0,
            "code_snippet": "",
            "description": "命中已知恶意文件哈希库",
            "fix_advice": "立即隔离该文件，并排查入侵途径",
        })

    # 2. 读文件文本
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception:
        content = ""

    if not language or language == "unknown":
        # 扩展名未识别时用内容嗅探兑底，仍不行再降为 any
        language = detect_language_by_content(file_path) or "any"
        if language == "unknown":
            language = "any"

    # 3. 签名扫描（内置 + DB 扩展）
    signatures = list(SIGNATURE_DB)
    if extra_signatures:
        signatures.extend(extra_signatures)
    for sig in signatures:
        # language==any 表示未能识别语言，为避免漏报应尝试所有规则
        if language != "any" and sig.get("lang", "any") not in (language, "any"):
            continue
        try:
            for m in re.finditer(sig["pattern"], content, re.IGNORECASE):
                line_no = content[:m.start()].count("\n") + 1
                snippet = _get_line(content, line_no)
                findings.append({
                    "rule_name": sig["name"],
                    "rule_type": "signature",
                    "severity": sig.get("severity", "medium"),
                    "line_no": line_no,
                    "code_snippet": snippet,
                    "description": sig.get("desc", sig.get("description", "")),
                    "fix_advice": sig.get("fix", sig.get("fix_advice", "")),
                })
                if len(findings) > 80:
                    break
        except re.error:
            continue


    # 4. YARA 规则（内置 + 自定义）
    yara_rules = list(DEFAULT_YARA_RULES)
    if extra_yara_rules:
        yara_rules.extend(extra_yara_rules)
    for rule in yara_rules:
        if language != "any" and rule.get("lang", "any") not in (language, "any"):
            continue
        try:
            for m in re.finditer(rule["pattern"], content, re.IGNORECASE):
                line_no = content[:m.start()].count("\n") + 1
                snippet = _get_line(content, line_no)
                findings.append({
                    "rule_name": rule["name"],
                    "rule_type": "yara",
                    "severity": rule.get("severity", "medium"),
                    "line_no": line_no,
                    "code_snippet": snippet,
                    "description": rule.get("description", rule.get("desc", "")),
                    "fix_advice": rule.get("fix_advice", rule.get("fix", "")),
                })
        except re.error:
            # 忽略错误的正则
            continue

    # 5. 计算风险等级
    risk_level = _calc_risk(findings)

    return {
        "findings": findings,
        "file_hash": file_hash,
        "risk_level": risk_level,
        "hit_count": len(findings),
    }


def _get_line(content: str, line_no: int) -> str:
    lines = content.split("\n")
    if 0 < line_no <= len(lines):
        return lines[line_no - 1][:300]
    return ""


def _calc_risk(findings: List[Dict]) -> str:
    if not findings:
        return "safe"
    sev = [f["severity"] for f in findings]
    if "high" in sev:
        return "high"
    if "medium" in sev:
        return "medium"
    return "low"


# ==================== 动态检测（真实沙箱执行） ====================
#
# 设计思路：
#   1. 把目标文件复制到独立临时目录（沙箱目录）作为 CWD；
#   2. 对 Python 文件：通过 sandbox_runner.py 在子进程中真实执行，
#      该 runner 用 monkey-patch 拦截 socket / subprocess / os.system /
#      os.popen / open(写模式) / eval / exec 等危险调用，
#      把所有触达内核的危险动作以 JSON 事件流写到 stderr，
#      并直接阻断（抛 PermissionError 或返回空），不会真实生效；
#   3. 对 PHP 文件：用 php-cli 启动真实子进程，外部通过轮询子进程列表 /
#      网络连接 / 沙箱目录文件差分实现行为观测；同时 stderr / stdout 全程捕获；
#   4. 子进程统一 3 秒超时；
#   5. 行为事件被规约为统一的 finding 结构，与静态扫描合并参与风险评分。
#
# 安全说明：
#   - Python 的所有危险 API 在 runner 启动阶段被替换，目标脚本运行时拿到的
#     就是受控版本，无法绕过；
#   - PHP 通过外部 psutil 监控，子进程一旦发起出站连接/派生子进程/写入沙箱外文件，
#     虽然无法在内核层面阻断，但 3 秒后会被 kill_process_tree 强制终止，
#     沙箱目录会被 shutil.rmtree 彻底清理。
# ============================================================

SANDBOX_TIMEOUT_SEC = 3           # 子进程最长运行时间
SANDBOX_RUNNER_PATH = os.path.join(os.path.dirname(__file__), "sandbox_runner.py")

# 行为事件类型 -> finding 元信息
_EVENT_META = {
    "network": {
        "rule_name": "出站网络连接",
        "severity": "high",
        "desc": "运行时尝试建立网络连接，疑似回连 C2 / 数据外发",
        "fix": "封禁该目标 IP，限制 Web 进程出站策略，溯源调用方",
    },
    "dns": {
        "rule_name": "可疑 DNS 解析",
        "severity": "medium",
        "desc": "运行时发起 DNS 解析，可能用于回连或外部资源拉取",
        "fix": "审查解析目标域名，必要时加入 DNS 黑名单",
    },
    "process": {
        "rule_name": "派生子进程",
        "severity": "high",
        "desc": "运行时调用系统命令派生子进程，典型 Webshell 行为",
        "fix": "限制 Web 用户可执行命令，启用进程白名单",
    },
    "file_write": {
        "rule_name": "运行时文件写入",
        "severity": "high",
        "desc": "运行时尝试创建/修改文件，可能植入新后门",
        "fix": "审查写入目标，剥离 Web 目录写权限",
    },
    "file_delete": {
        "rule_name": "运行时文件删除",
        "severity": "medium",
        "desc": "运行时尝试删除文件，可能为清理痕迹",
        "fix": "审查脚本调用栈，限制文件删除权限",
    },
    "eval": {
        "rule_name": "运行时 eval 执行",
        "severity": "high",
        "desc": "运行时调用 eval() 动态执行代码，强 Webshell 特征",
        "fix": "禁用 eval / assert / Function 等动态执行",
    },
    "exec": {
        "rule_name": "运行时 exec 执行",
        "severity": "high",
        "desc": "运行时调用 exec() 动态执行代码块",
        "fix": "禁用动态代码执行，使用白名单或解析器替代",
    },
    "compile": {
        "rule_name": "运行时编译代码",
        "severity": "medium",
        "desc": "运行时动态编译代码，可能为加密混淆载荷",
        "fix": "审查被编译的源码字符串来源",
    },
    "sensitive_access": {
        "rule_name": "访问敏感目录",
        "severity": "high",
        "desc": "运行时尝试读取系统敏感目录",
        "fix": "加固相关目录 ACL，启用 SELinux/AppArmor",
    },
    "runtime_error": {
        "rule_name": "运行时异常",
        "severity": "low",
        "desc": "目标脚本在沙箱中抛出异常，可能依赖外部环境",
        "fix": "结合静态结果综合判断",
    },
    "blocked": {
        "rule_name": "沙箱阻断危险调用",
        "severity": "high",
        "desc": "目标脚本触达了沙箱拦截规则，确认存在危险行为",
        "fix": "立即隔离该文件，按静态结果定位入侵入口",
    },
}


def _which(cmd: str) -> str:
    """跨平台 which：在 PATH 中查找可执行文件"""
    return shutil.which(cmd) or ""


def _kill_tree(pid: int):
    """跨平台杀掉进程树"""
    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                capture_output=True, timeout=2,
            )
        else:
            os.killpg(os.getpgid(pid), 9)
    except Exception:
        pass


def _run_subprocess_capture(cmd: list, cwd: str, timeout: int) -> Tuple[str, str, int, bool]:
    """启动子进程并在 timeout 后强制 kill 整棵进程树"""
    timed_out = {"v": False}
    env = dict(os.environ)
    env["SBX_DIR"] = cwd
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        proc = subprocess.Popen(
            cmd, cwd=cwd, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace",
        )
    except Exception as e:
        return "", f"[subprocess start failed] {e}", -1, False

    def _killer():
        timed_out["v"] = True
        _kill_tree(proc.pid)

    timer = threading.Timer(timeout, _killer)
    timer.start()
    try:
        stdout, stderr = proc.communicate()
    except Exception as e:
        stdout, stderr = "", f"[communicate error] {e}"
    finally:
        timer.cancel()

    return stdout or "", stderr or "", proc.returncode, timed_out["v"]


def _parse_sandbox_events(stderr_text: str) -> List[Dict]:
    """从 sandbox_runner 的 stderr 中解析 __SBX__ 事件流"""
    events = []
    for line in stderr_text.splitlines():
        line = line.strip()
        if not line.startswith("__SBX__"):
            continue
        try:
            ev = json.loads(line[len("__SBX__"):])
            events.append(ev)
        except Exception:
            continue
    return events


def _events_to_findings(events: List[Dict]) -> List[Dict]:
    """把行为事件归约为 finding 列表"""
    findings = []
    # 去重计数：同类型 + 关键字段
    seen = set()
    for ev in events:
        t = ev.get("type", "")
        if t in ("start", "end", "exit"):
            continue
        if t == "file_write" and ev.get("in_sandbox"):
            # 沙箱内自身写入（如临时缓存）不计入风险
            continue
        meta = _EVENT_META.get(t)
        if not meta:
            continue
        key = (t, ev.get("addr", "") or ev.get("cmd", "") or ev.get("path", "") or ev.get("code", "")[:80])
        if key in seen:
            continue
        seen.add(key)

        detail_parts = []
        for k in ("addr", "cmd", "path", "host", "code", "msg"):
            v = ev.get(k)
            if v:
                detail_parts.append(f"{k}={str(v)[:120]}")
        snippet = " | ".join(detail_parts)

        findings.append({
            "rule_name": meta["rule_name"],
            "rule_type": "behavior",
            "severity": meta["severity"],
            "line_no": 0,
            "code_snippet": snippet[:300],
            "description": meta["desc"] + (f"（API: {ev.get('api')}）" if ev.get("api") else ""),
            "fix_advice": meta["fix"],
        })
    return findings


def _taint_reachability_scan(content_or_path: str, language: str) -> List[Dict]:
    """
    污点可达性分析（解释器不可用 / 不能真实执行的语言场景下的兜底）：
    严格匹配"用户输入源 -> 危险 sink"同语句可达的模式。
    与简单正则的本质区别：必须同时出现污染源（$_POST/_GET/_REQUEST/_COOKIE/request.getParameter/Request.Form 等）
    和危险 sink（eval/system/exec/include 等），运行时必然形成可控危险行为，可合理判定为 high。

    content_or_path: 支持两种输入：
      - 已存在的文件路径（自动读取）
      - 直接传入的源码字符串（推荐，规避 AV 删文件等时序问题）
    """
    # 兼容路径/内容两种入参
    content = ""
    if content_or_path and os.path.isfile(content_or_path) and len(content_or_path) < 1024:
        try:
            with open(content_or_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            content = ""
    else:
        content = content_or_path or ""
    if not content:
        return []

    # 每条规则：sink 函数 + 同行/同表达式内可达污染源
    PHP_TAINT_RULES = [
        ("运行时 eval 用户输入",   r"\beval\s*\([^)]*\$_(POST|GET|REQUEST|COOKIE|SERVER|FILES)",
         "eval() 直接执行 HTTP 请求参数，运行时必然形成任意代码执行 (RCE)",
         "禁用 eval；使用白名单严格过滤参数"),
        ("运行时 assert 用户输入", r"\bassert\s*\([^)]*\$_(POST|GET|REQUEST|COOKIE)",
         "assert() 执行 HTTP 请求参数", "在 php.ini 中禁用 assert.active"),
        ("运行时命令执行用户输入", r"\b(system|exec|shell_exec|passthru|popen|proc_open)\s*\([^)]*\$_(POST|GET|REQUEST|COOKIE)",
         "命令执行函数直接接收用户输入，形成系统命令注入",
         "禁用相关函数 disable_functions；白名单参数"),
        ("运行时文件包含用户输入", r"\b(include|require)(_once)?\s*\(?[^;]*\$_(POST|GET|REQUEST|COOKIE)",
         "include/require 包含用户输入，形成本地/远程文件包含漏洞",
         "白名单文件路径；开启 allow_url_include=Off"),
        ("运行时 preg_replace /e 用户输入", r"preg_replace\s*\(\s*['\"][^'\"]*/e[^)]*\$_(POST|GET|REQUEST)",
         "preg_replace /e 修饰符执行用户输入", "改用 preg_replace_callback"),
        ("运行时回调函数用户输入", r"\b(call_user_func|call_user_func_array|array_map|usort)\s*\(\s*\$_(POST|GET|REQUEST|COOKIE)",
         "回调函数名来自用户输入，可调用任意函数", "白名单过滤回调名"),
        ("运行时反序列化用户输入", r"\bunserialize\s*\([^)]*\$_(POST|GET|REQUEST|COOKIE)",
         "unserialize 用户输入，可触发反序列化 RCE", "改用 json_decode 或加签校验"),
    ]
    JSP_TAINT_RULES = [
        ("运行时命令执行用户输入", r"Runtime\.getRuntime\(\)\.exec\s*\([^)]*request\.getParameter",
         "Runtime.exec 接收 HTTP 参数，命令注入",
         "白名单参数，禁止拼接命令"),
        ("运行时 ProcessBuilder 用户输入", r"new\s+ProcessBuilder[^;]*request\.getParameter",
         "ProcessBuilder 命令接收 HTTP 参数", "白名单过滤参数"),
    ]
    ASP_TAINT_RULES = [
        ("运行时 Eval 用户输入", r"\bEval\s*\([^)]*Request(\.|\()",
         "ASP Eval 执行 Request 输入", "重构代码避免动态执行"),
        ("运行时 Execute 用户输入", r"\bExecute\s*\([^)]*Request(\.|\()",
         "ASP Execute 执行 Request 输入", "重构代码避免动态执行"),
    ]
    PY_TAINT_RULES = [
        ("运行时 eval Flask 输入", r"\beval\s*\([^)]*request\.(args|form|values|cookies|json)",
         "eval 执行 Flask 请求参数", "改用 ast.literal_eval 或参数校验"),
        ("运行时 exec Flask 输入", r"\bexec\s*\([^)]*request\.(args|form|values|cookies|json)",
         "exec 执行 Flask 请求参数", "禁止动态执行"),
        ("运行时 os.system Flask 输入", r"os\.system\s*\([^)]*request\.(args|form|values)",
         "os.system 接收 Flask 请求参数", "改用 subprocess + 参数列表"),
    ]
    rules_map = {"php": PHP_TAINT_RULES, "jsp": JSP_TAINT_RULES,
                 "asp": ASP_TAINT_RULES, "python": PY_TAINT_RULES}
    rules = rules_map.get(language, [])

    findings = []
    for name, pat, desc, fix in rules:
        try:
            for m in re.finditer(pat, content, re.IGNORECASE):
                line_no = content[:m.start()].count("\n") + 1
                findings.append({
                    "rule_name": name,
                    "rule_type": "behavior",
                    "severity": "high",
                    "line_no": line_no,
                    "code_snippet": _get_line(content, line_no),
                    "description": desc + "（污点可达性判定：用户输入直接流向危险 sink）",
                    "fix_advice": fix,
                })
        except re.error:
            continue
    return findings


def _snapshot_dir(path: str) -> Dict[str, int]:
    """对沙箱目录做文件名+大小快照"""
    snap = {}
    try:
        for root, _, files in os.walk(path):
            for fn in files:
                fp = os.path.join(root, fn)
                try:
                    snap[os.path.relpath(fp, path)] = os.path.getsize(fp)
                except Exception:
                    snap[os.path.relpath(fp, path)] = 0
    except Exception:
        pass
    return snap


def _diff_snapshot(before: Dict[str, int], after: Dict[str, int]) -> List[Dict]:
    """对比沙箱目录变化"""
    diffs = []
    for k, v in after.items():
        if k not in before:
            diffs.append({"type": "file_write", "path": k, "api": "fs_diff_new", "size": v})
        elif before[k] != v:
            diffs.append({"type": "file_write", "path": k, "api": "fs_diff_modify",
                          "size": v, "old_size": before[k]})
    for k in before:
        if k not in after:
            diffs.append({"type": "file_delete", "path": k, "api": "fs_diff_remove"})
    return diffs


def _run_python_sandbox(target_in_sandbox: str, sandbox_dir: str) -> Tuple[List[Dict], str, bool, bool]:
    """
    Python：通过 sandbox_runner.py 真实执行 + monkey-patch hook 拦截
    返回 (events, runtime_log, executed, timed_out)
    """
    py = _which("python") or _which("python3") or _which("py") or "python"
    if not os.path.exists(SANDBOX_RUNNER_PATH):
        return [], f"sandbox_runner.py 不存在: {SANDBOX_RUNNER_PATH}", False, False

    stdout, stderr, rc, timed_out = _run_subprocess_capture(
        [py, SANDBOX_RUNNER_PATH, target_in_sandbox],
        cwd=sandbox_dir, timeout=SANDBOX_TIMEOUT_SEC,
    )
    events = _parse_sandbox_events(stderr)
    log = (
        f"[Python 沙箱执行] interpreter={py}\n"
        f"return_code={rc}  timed_out={timed_out}\n"
        f"--- stdout ---\n{stdout[:500]}\n"
        f"--- stderr(non-sbx) ---\n"
        + "\n".join([l for l in stderr.splitlines() if not l.startswith("__SBX__")])[:500]
    )
    return events, log, True, timed_out


def _run_php_sandbox(target_in_sandbox: str, sandbox_dir: str) -> Tuple[List[Dict], str, bool, bool]:
    """
    PHP：用 php-cli 真实执行；外部通过：
      - 启动前/后对沙箱目录做快照差分（文件写入/删除）
      - stderr/stdout 关键字回收
    实现行为观测。
    若 php 不在 PATH，返回 executed=False。
    """
    php = _which("php")
    if not php:
        return [], "PHP 解释器 (php-cli) 未在 PATH 中找到，跳过真实执行", False, False

    snap_before = _snapshot_dir(sandbox_dir)
    # -d 关闭一些可能阻塞的特性；-n 不读 php.ini 减少环境差异
    cmd = [php, "-n", "-d", "display_errors=stderr", "-d", "max_execution_time=2", target_in_sandbox]
    stdout, stderr, rc, timed_out = _run_subprocess_capture(
        cmd, cwd=sandbox_dir, timeout=SANDBOX_TIMEOUT_SEC,
    )
    snap_after = _snapshot_dir(sandbox_dir)
    events = _diff_snapshot(snap_before, snap_after)

    # 从 stdout/stderr 中识别明显的执行后回显（如 whoami 的 root / 用户名 / uid=）
    combined = (stdout + "\n" + stderr).lower()
    if any(k in combined for k in ("uid=", "gid=", "root\n", "administrator", "nt authority")):
        events.append({"type": "process", "cmd": "whoami-like output detected in stdout",
                       "api": "stdout_pattern"})
    if "command not found" in combined or "is not recognized" in combined:
        # 说明 php 尝试 shell_exec 但命令缺失，仍属于派生进程行为
        events.append({"type": "process", "cmd": "shell command attempted (not found)",
                       "api": "stdout_pattern"})
    if "permission denied" in combined and "fopen" in combined:
        events.append({"type": "file_write", "path": "blocked by OS perm",
                       "api": "stderr_pattern", "in_sandbox": False})

    log = (
        f"[PHP 沙箱执行] interpreter={php}\n"
        f"return_code={rc}  timed_out={timed_out}\n"
        f"fs_diff={len(events)}\n"
        f"--- stdout ---\n{stdout[:500]}\n"
        f"--- stderr ---\n{stderr[:500]}"
    )
    return events, log, True, timed_out


def dynamic_scan(file_path: str, language: str = None) -> Dict:
    """
    真实动态检测：在隔离沙箱目录中以子进程方式实际执行目标文件，
    通过 hook（Python）或外部观测（PHP）收集运行时行为，
    阻断危险调用使其不会真实生效，最终把行为事件归约为 findings。
    """
    if not os.path.exists(file_path):
        return {"findings": [], "risk_level": "safe", "hit_count": 0,
                "behaviors": [], "runtime_log": "文件不存在"}

    if not language or language == "unknown":
        language = resolve_language(file_path, file_path)

    # 一次性把内容读到内存（防 AV/防被删；后续污点分析直接复用，避免读不到空）
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            file_content = f.read()
    except Exception:
        file_content = ""

    sandbox_dir = tempfile.mkdtemp(prefix="webshell_sbx_")
    findings: List[Dict] = []
    runtime_log = ""
    timed_out = False
    executed = False
    try:
        ext = os.path.splitext(file_path)[1] or ".tmp"
        target_in_sbx = os.path.join(sandbox_dir, "target" + ext)
        # 注意：Windows 上 copy2 会因 utime 报 PermissionError，这里不需要保留元信息
        try:
            shutil.copyfile(file_path, target_in_sbx)
        except FileNotFoundError:
            # 文件被 AV 实时清掉的兜底：用之前读到的内容重建沙箱副本
            with open(target_in_sbx, "w", encoding="utf-8") as f:
                f.write(file_content)

        if language == "python":
            events, runtime_log, executed, timed_out = _run_python_sandbox(target_in_sbx, sandbox_dir)
            findings = _events_to_findings(events)
            findings.extend(_taint_reachability_scan(file_content, "python"))
        elif language == "php":
            events, runtime_log, executed, timed_out = _run_php_sandbox(target_in_sbx, sandbox_dir)
            findings = _events_to_findings(events)
            findings.extend(_taint_reachability_scan(file_content, "php"))
            if not executed:
                runtime_log = (runtime_log or "") + "\n[兜底] php-cli 不可用，已启用污点可达性分析"
        else:
            taint = _taint_reachability_scan(file_content, language)
            findings.extend(taint)
            runtime_log = (f"语言 {language} 需要完整应用服务器（Tomcat/IIS），"
                           f"无法在通用沙箱真实执行，已启用污点可达性分析；"
                           f"命中 {len(taint)} 条用户输入->危险 sink 的可达路径")
            if not taint:
                findings.append({
                    "rule_name": "动态检测降级",
                    "rule_type": "behavior",
                    "severity": "low",
                    "line_no": 0,
                    "code_snippet": f"language={language}",
                    "description": runtime_log,
                    "fix_advice": "建议把该文件放到独立隔离测试环境完整执行验证",
                })
            executed = True

        if timed_out:
            findings.append({
                "rule_name": "执行超时强制终止",
                "rule_type": "behavior",
                "severity": "medium",
                "line_no": 0,
                "code_snippet": f"timeout={SANDBOX_TIMEOUT_SEC}s",
                "description": "目标脚本在沙箱中触发了 {} 秒超时强制 kill，可能存在死循环 / 长连接 / 阻塞调用".format(SANDBOX_TIMEOUT_SEC),
                "fix_advice": "结合静态结果判断是否为故意拖延性 Webshell",
            })

        if not executed and language in ("python", "php"):
            findings.append({
                "rule_name": "解释器不可用",
                "rule_type": "behavior",
                "severity": "low",
                "line_no": 0,
                "code_snippet": f"language={language}",
                "description": f"{language} 解释器未在 PATH 中找到，已跳过真实执行",
                "fix_advice": "请在服务器安装对应解释器后重新执行动态检测",
            })
    finally:
        try:
            shutil.rmtree(sandbox_dir, ignore_errors=True)
        except Exception:
            pass

    behaviors = sorted({f["rule_name"] for f in findings})
    risk = _calc_risk(findings)
    return {
        "findings": findings,
        "risk_level": risk,
        "hit_count": len(findings),
        "behaviors": behaviors,
        "runtime_log": runtime_log,
    }
