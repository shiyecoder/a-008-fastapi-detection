"""文件上传公共工具"""
import os
import uuid
from datetime import datetime
from fastapi import UploadFile
from .config import settings


def save_upload_file(file: UploadFile, sub_dir: str) -> dict:
    """
    保存上传文件到 D:\Webshell检测平台的设计与实现\<sub_dir>\YYYYMM\
    返回 { rel_path, abs_path, file_name, size }
    """
    today = datetime.now().strftime("%Y%m")
    target_dir = os.path.join(settings.UPLOAD_ROOT, sub_dir, today)
    os.makedirs(target_dir, exist_ok=True)

    ext = os.path.splitext(file.filename)[1]
    new_name = f"{uuid.uuid4().hex}{ext}"
    abs_path = os.path.join(target_dir, new_name)

    content = file.file.read()
    with open(abs_path, "wb") as f:
        f.write(content)

    rel_path = f"{sub_dir}/{today}/{new_name}".replace("\\", "/")
    return {
        "rel_path": rel_path,
        "abs_path": abs_path,
        "file_name": file.filename,
        "size": len(content),
    }


def abs_path_of(rel_path: str) -> str:
    """根据相对路径获取绝对路径"""
    return os.path.join(settings.UPLOAD_ROOT, rel_path.replace("/", os.sep))
