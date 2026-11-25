"""
应用配置
- 端口固定使用 8080
- 数据库密码 123456
- 文件上传目录: D:\Webshell检测平台的设计与实现
"""
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    # 应用
    APP_NAME: str = "Webshell检测平台"
    PORT: int = 8080

    # 数据库（MySQL）
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "123456"
    DB_NAME: str = "webshell_platform"

    # JWT
    JWT_SECRET: str = "webshell-platform-secret-key-2026"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天

    # 文件上传
    UPLOAD_ROOT: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')

    # 上传子目录
    AVATAR_DIR: str = "avatars"
    DETECTION_DIR: str = "detection"
    QUARANTINE_DIR: str = "quarantine"

    @property
    def DB_URL(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )


settings = Settings()

# 确保上传目录存在
for sub in [settings.AVATAR_DIR, settings.DETECTION_DIR, settings.QUARANTINE_DIR]:
    os.makedirs(os.path.join(settings.UPLOAD_ROOT, sub), exist_ok=True)
