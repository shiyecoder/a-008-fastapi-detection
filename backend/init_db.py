"""
数据库初始化（用 ORM create_all 建表）：
1. 创建数据库（若不存在）
2. drop_all + create_all
3. 运行 seed_data.py 插入测试数据
4. 把所有用户密码替换为 bcrypt('123456')
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    os.chdir(here)

    import pymysql
    from app.config import settings
    from app.security import hash_password

    # 1. 创建数据库
    conn = pymysql.connect(host=settings.DB_HOST, port=settings.DB_PORT,
                           user=settings.DB_USER, password=settings.DB_PASSWORD,
                           charset="utf8mb4", autocommit=True)
    with conn.cursor() as cur:
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{settings.DB_NAME}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    conn.close()

    # 2. ORM 建表
    from app.database import Base, engine
    from app import models  # noqa: F401
    print("DROP & CREATE 所有表...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("表结构创建完成")

    # 3. 插入种子数据
    print("插入种子数据...")
    import subprocess
    r = subprocess.run([sys.executable, "seed_data.py"], cwd=here)
    if r.returncode != 0:
        raise RuntimeError("seed_data.py 失败")

    # 4. 更新密码
    print("更新密码为 bcrypt('123456')...")
    pwd = hash_password("123456")
    conn = pymysql.connect(host=settings.DB_HOST, port=settings.DB_PORT,
                           user=settings.DB_USER, password=settings.DB_PASSWORD,
                           database=settings.DB_NAME, charset="utf8mb4", autocommit=True)
    with conn.cursor() as cur:
        cur.execute("UPDATE sys_user SET password=%s", (pwd,))
    conn.close()
    print("数据库初始化完成 ✓")


if __name__ == "__main__":
    main()
