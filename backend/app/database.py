"""数据库连接与基础模型"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

# 创建引擎，开启 pool_pre_ping 避免连接断开
engine = create_engine(
    settings.DB_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI 依赖：获取数据库 Session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
