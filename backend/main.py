"""
Webshell检测平台 - FastAPI 主入口
端口固定 8080
"""
import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.database import Base, engine
from app.log_middleware import AccessLogMiddleware
from app.api import (
    auth, profile, user, role, menu, dashboard,
    detection, yara_rule, quarantine, alert,
    vuln_fix, report, log, signature, hash_lib,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("webshell-platform")

app = FastAPI(title=settings.APP_NAME, version="1.0.0")

# 访问日志中间件（自动记录写操作）
app.add_middleware(AccessLogMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局异常处理：返回统一格式
@app.exception_handler(Exception)
async def all_exception_handler(req: Request, exc: Exception):
    logger.exception(exc)
    return JSONResponse(status_code=200, content={"code": 500, "msg": str(exc), "data": None})


@app.exception_handler(SQLAlchemyError)
async def db_exception_handler(req: Request, exc: SQLAlchemyError):
    logger.exception(exc)
    return JSONResponse(status_code=200, content={"code": 500, "msg": "数据库错误", "data": None})


# 静态资源：上传目录直接对外提供
os.makedirs(settings.UPLOAD_ROOT, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_ROOT), name="uploads")


# 路由聚合，统一前缀 /api
PREFIX = "/api"
for r in [auth.router, profile.router, user.router, role.router, menu.router,
          dashboard.router, detection.router, yara_rule.router, quarantine.router,
          alert.router, vuln_fix.router,
          report.router, log.router, signature.router, hash_lib.router]:
    app.include_router(r, prefix=PREFIX)


@app.get("/")
def root():
    return {"app": settings.APP_NAME, "status": "running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=False)
