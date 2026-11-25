"""统一响应封装"""
from typing import Any, Optional
from pydantic import BaseModel


class R(BaseModel):
    """统一响应格式 { code, msg, data }"""
    code: int = 200
    msg: str = "success"
    data: Optional[Any] = None


def ok(data: Any = None, msg: str = "success") -> dict:
    return {"code": 200, "msg": msg, "data": data}


def fail(msg: str = "error", code: int = 400, data: Any = None) -> dict:
    return {"code": code, "msg": msg, "data": data}


def page_data(items: list, total: int, page: int, page_size: int) -> dict:
    """分页结构"""
    return {
        "list": items,
        "total": total,
        "page": page,
        "pageSize": page_size,
    }
