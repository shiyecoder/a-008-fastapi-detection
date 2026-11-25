"""种子数据 - 主入口"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pymysql
from app.config import settings


def get_conn(with_db=True):
    kw = dict(host=settings.DB_HOST, port=settings.DB_PORT,
              user=settings.DB_USER, password=settings.DB_PASSWORD,
              charset="utf8mb4", autocommit=True)
    if with_db:
        kw["database"] = settings.DB_NAME
    return pymysql.connect(**kw)


def seed():
    from seed_part1 import seed_users_roles_menus
    from seed_part2 import seed_yara_vuln
    from seed_part3 import seed_detection
    from seed_part5 import seed_alert_report_log
    conn = get_conn()
    try:
        seed_users_roles_menus(conn)
        seed_yara_vuln(conn)
        seed_detection(conn)
        seed_alert_report_log(conn)
    finally:
        conn.close()
    print("种子数据插入完成")


if __name__ == "__main__":
    seed()
