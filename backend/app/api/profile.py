"""个人信息：修改资料、修改密码、上传头像"""
from fastapi import APIRouter, Depends, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import get_current_user
from ..models import SysUser
from ..response import ok, fail
from ..security import hash_password, verify_password
from ..upload_util import save_upload_file
from ..config import settings

router = APIRouter(prefix="/profile", tags=["个人中心"])


class ProfileUpdate(BaseModel):
    nickname: str | None = None
    email: str | None = None
    phone: str | None = None


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


@router.put("/update")
def update_profile(body: ProfileUpdate, current=Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(SysUser).get(current.id)
    if body.nickname is not None:
        user.nickname = body.nickname
    if body.email is not None:
        user.email = body.email
    if body.phone is not None:
        user.phone = body.phone
    db.commit()
    return ok(msg="修改成功")


@router.put("/password")
def change_password(body: PasswordChange, current=Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(SysUser).get(current.id)
    if not verify_password(body.old_password, user.password):
        return fail("原密码错误")
    user.password = hash_password(body.new_password)
    db.commit()
    return ok(msg="密码修改成功")


@router.post("/avatar")
def upload_avatar(file: UploadFile = File(...), current=Depends(get_current_user), db: Session = Depends(get_db)):
    """上传头像，保存到 D 盘同名目录的 avatars 子目录"""
    info = save_upload_file(file, settings.AVATAR_DIR)
    user = db.query(SysUser).get(current.id)
    user.avatar = info["rel_path"]
    db.commit()
    return ok({"avatar": info["rel_path"]})
