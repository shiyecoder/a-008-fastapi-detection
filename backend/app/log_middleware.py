"""
访问日志中间件：自动写入 sys_log 表
- 仅记录 POST/PUT/DELETE 等写操作（GET 不记录避免噪声）
- 解析 Authorization 头获得当前用户
- 登录请求从请求体获取 username
"""
import json
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Message
from .database import SessionLocal
from .models import SysLog
from .security import decode_token

logger = logging.getLogger("access-log")

# 路径前缀 → 模块（中文）
MODULE_MAP = [
    ("/auth", "认证"),
    ("/profile", "系统"),
    ("/user", "系统"),
    ("/role", "系统"),
    ("/menu", "系统"),
    ("/log", "系统"),
    ("/dashboard", "系统"),
    ("/detection", "检测"),
    ("/yara", "检测"),
    ("/signature", "检测"),
    ("/hash-lib", "检测"),
    ("/quarantine", "隔离"),
    ("/alert", "告警"),
    ("/vuln-fix", "告警"),
    ("/report", "报告"),
]

# 路径片段 → 中文操作
OP_KEYWORDS = [
    ("/login", "登录"),
    ("/logout", "登出"),
    ("/register", "注册"),
    ("/password", "修改密码"),
    ("/avatar", "上传头像"),
    ("/reset-password", "重置密码"),
    ("/assign-menu", "分配菜单"),
    ("/scan", "执行检测"),
    ("/quarantine/", "隔离文件"),
    ("/restore/", "还原隔离文件"),
    ("/handle/", "处理告警"),
    ("/generate", "生成报告"),
    ("/clear", "清空"),
    ("/toggle/", "切换状态"),
    ("/add", "新增"),
    ("/update/", "修改"),
    ("/delete/", "删除"),
    ("/update", "修改"),
    ("/delete", "删除"),
]

# 不记录的写操作路径（噪声接口）
SKIP_PREFIX = ()


def _resolve_module(path: str) -> str:
    for prefix, name in MODULE_MAP:
        if path.startswith(prefix):
            return name
    return "其他"


def _resolve_operation(method: str, path: str) -> str:
    for kw, name in OP_KEYWORDS:
        if kw in path:
            return name
    return {"POST": "新建", "PUT": "更新", "DELETE": "删除"}.get(method, method)


class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        path = request.url.path
        method = request.method

        record = (
            path.startswith("/api")
            and method in ("POST", "PUT", "DELETE", "PATCH")
            and not any(path.startswith(s) for s in SKIP_PREFIX)
        )

        # 解析 Token 获取用户
        user_id = None
        username = None
        if record:
            auth = request.headers.get("authorization") or ""
            if auth.startswith("Bearer "):
                payload = decode_token(auth[len("Bearer "):].strip())
                if payload:
                    user_id = payload.get("uid")
                    username = payload.get("username")

        # 登录请求：从 body 拿 username（不影响下游再读取 body）
        login_username = None
        if record and path == "/api/auth/login":
            try:
                body_bytes = await request.body()

                async def _receive() -> Message:
                    return {"type": "http.request", "body": body_bytes, "more_body": False}

                request._receive = _receive  # 让下游 handler 仍能读到 body
                if body_bytes:
                    d = json.loads(body_bytes)
                    login_username = d.get("username")
            except Exception:
                pass

        response = await call_next(request)

        if record:
            try:
                rel = path[4:]  # 去掉 /api 前缀用于映射
                module = _resolve_module(rel)
                operation = _resolve_operation(method, rel)
                ip = request.client.host if request.client else None
                final_user = username or login_username or "(匿名)"
                status_ok = 1 if response.status_code < 400 else 0

                # 关键写操作（登录/注册）需读响应 body 判断业务 code
                if path in ("/api/auth/login", "/api/auth/register"):
                    body_chunks = [chunk async for chunk in response.body_iterator]
                    body_bytes = b"".join(body_chunks)
                    try:
                        d = json.loads(body_bytes or b"{}")
                        if isinstance(d, dict) and d.get("code") not in (None, 200):
                            status_ok = 0
                    except Exception:
                        pass
                    # 重建响应以便下发给客户端
                    from starlette.responses import Response
                    response = Response(
                        content=body_bytes,
                        status_code=response.status_code,
                        headers={k: v for k, v in response.headers.items()
                                 if k.lower() not in ("content-length",)},
                        media_type=response.media_type,
                    )

                db = SessionLocal()
                try:
                    db.add(SysLog(
                        user_id=user_id, username=final_user,
                        module=module, operation=operation,
                        method=method, url=path,
                        ip=ip, status=status_ok,
                    ))
                    db.commit()
                finally:
                    db.close()
            except Exception as e:
                logger.warning("access log failed: %s", e)

        return response
