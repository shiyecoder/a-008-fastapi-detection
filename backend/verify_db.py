import pymysql
from app.config import settings
from app.security import verify_password
conn=pymysql.connect(host=settings.DB_HOST,port=settings.DB_PORT,user=settings.DB_USER,password=settings.DB_PASSWORD,database=settings.DB_NAME,charset='utf8mb4')
c=conn.cursor()
for t in ['sys_user','sys_role','sys_menu','sys_user_role','sys_role_menu','sys_log','detection_task','detection_result','yara_rule','quarantine_file','alert','vuln_fix_mapping','report']:
    c.execute(f'SELECT COUNT(*) FROM `{t}`')
    print(f'{t:25s} = {c.fetchone()[0]}')
c.execute("SELECT password FROM sys_user WHERE username='admin'")
pw=c.fetchone()[0]
print('admin/123456 verify =', verify_password('123456', pw))
