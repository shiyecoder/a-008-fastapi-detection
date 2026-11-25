"""种子数据 part5: 告警/报告/操作日志（匹配 ORM）"""

def seed_alert_report_log(conn):
    cur = conn.cursor()

    # alert(title, alert_type, severity, source, description, status, handler, handle_remark, handle_time, create_time)
    alerts = [
        ('Webshell检出-shell.php', 'webshell', 'high', 'detection_task#1', '检测到一句话木马', 'handled', 'admin', '已隔离并通知运维', '2025-12-08 11:00:00', '2025-12-08 10:23:13'),
        ('Webshell检出-cmd.jsp', 'webshell', 'high', 'detection_task#3', 'JSP命令执行后门', 'handled', 'security', '已删除文件', '2025-12-22 10:30:00', '2025-12-22 09:45:04'),
        ('Webshell检出-backdoor.php', 'webshell', 'high', 'detection_task#6', 'assert后门', 'handled', 'admin', '已恢复（误报）', '2026-01-10 10:00:00', '2026-01-10 09:12:23'),
        ('Webshell检出-eval.php', 'webshell', 'high', 'detection_task#8', 'eval一句话', 'pending', None, None, None, '2026-01-22 15:55:01'),
        ('Webshell检出-b64.php', 'webshell', 'high', 'detection_task#9', '混淆Webshell', 'handled', 'security', '已隔离', '2026-01-29 09:00:00', '2026-01-28 10:18:48'),
        ('Webshell检出-spy.jsp', 'webshell', 'high', 'detection_task#11', 'JSP命令执行', 'handled', 'admin', '已删除', '2026-02-08 10:30:00', '2026-02-08 09:35:54'),
        ('Webshell检出-attack.asp', 'webshell', 'high', 'detection_task#13', 'ASP一句话', 'handled', 'admin', '已隔离', '2026-02-21 09:00:00', '2026-02-20 15:30:03'),
        ('Webshell检出-mal.php', 'webshell', 'high', 'detection_task#15', 'Webshell', 'handled', 'admin', '已隔离', '2026-03-03 09:00:00', '2026-03-02 09:25:21'),
        ('Webshell检出-control.php', 'webshell', 'high', 'detection_task#20', '一句话木马', 'handled', 'admin', '已隔离', '2026-04-04 11:00:00', '2026-04-04 09:12:02'),
        ('Webshell检出-tunnel.jsp', 'webshell', 'high', 'detection_task#24', 'JSP隧道木马', 'pending', None, None, None, '2026-05-03 10:22:15'),
        ('Webshell检出-final.php', 'webshell', 'high', 'detection_task#25', 'eval一句话', 'pending', None, None, None, '2026-05-10 13:45:02'),
    ]
    cur.executemany("INSERT INTO alert (title, alert_type, severity, source, description, status, handler, handle_remark, handle_time, create_time) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", alerts)

    # report(title, report_type, related_task_id, risk_level, content, user_id, create_time)
    reports = [
        ('2025年12月检测报告', 'detection', 1, 'high', '本月共扫描15个文件，发现高危Webshell 5个', 1, '2025-12-31 10:00:00'),
        ('2026年1月月报', 'detection', None, 'high', '1月共检测25次，高危5次，已全部处置', 2, '2026-01-31 16:00:00'),
        ('2026年第1季度安全综合报告', 'detection', None, 'high', '季度Webshell拦截率99%', 1, '2026-04-01 10:00:00'),
        ('2026年2月月报', 'detection', None, 'medium', '2月新增4个Webshell拦截', 1, '2026-02-28 16:00:00'),
        ('2026年3月月报', 'detection', None, 'high', '3月Webshell事件4起', 2, '2026-03-31 17:00:00'),
        ('2026年4月月报', 'detection', None, 'high', '4月命令注入1起', 2, '2026-04-30 16:00:00'),
        ('2026年第2季度报告', 'detection', None, 'medium', '季度安全评估总结', 1, '2026-05-13 09:00:00'),
    ]
    cur.executemany("INSERT INTO report (title, report_type, related_task_id, risk_level, content, user_id, create_time) VALUES (%s,%s,%s,%s,%s,%s,%s)", reports)

    # sys_log(user_id, username, module, operation, method, url, ip, status, create_time)
    logs = [
        (1, 'admin', '认证', '登录', 'POST', '/api/auth/login', '192.168.1.10', 1, '2025-12-08 09:00:11'),
        (1, 'admin', '检测', '新建检测任务', 'POST', '/api/detection/scan', '192.168.1.10', 1, '2025-12-08 10:23:11'),
        (2, 'security', '认证', '登录', 'POST', '/api/auth/login', '192.168.1.20', 1, '2025-12-22 09:30:00'),
        (2, 'security', '检测', '新建检测任务', 'POST', '/api/detection/scan', '192.168.1.20', 1, '2025-12-22 09:45:00'),
        (2, 'security', '告警', '处置告警', 'PUT', '/api/alerts/2/handle', '192.168.1.20', 1, '2025-12-22 10:30:00'),
        (1, 'admin', '隔离', '恢复文件', 'PUT', '/api/quarantine/3/restore', '192.168.1.10', 1, '2026-01-10 10:00:00'),
        (1, 'admin', '认证', '登录', 'POST', '/api/auth/login', '192.168.1.10', 1, '2026-01-22 15:50:00'),
        (1, 'admin', '检测', '新建检测任务', 'POST', '/api/detection/scan', '192.168.1.10', 1, '2026-01-22 15:55:00'),
        (3, 'zhangsan', '认证', '登录失败', 'POST', '/api/auth/login', '192.168.1.30', 0, '2026-01-25 09:00:00'),
        (3, 'zhangsan', '认证', '登录', 'POST', '/api/auth/login', '192.168.1.30', 1, '2026-01-25 09:01:00'),
        (1, 'admin', '系统', '新增用户', 'POST', '/api/system/users', '192.168.1.10', 1, '2026-02-01 10:00:00'),
        (1, 'admin', '系统', '修改角色', 'PUT', '/api/system/roles/2', '192.168.1.10', 1, '2026-02-01 10:30:00'),
        (2, 'security', 'YARA', '新增规则', 'POST', '/api/detection/yara', '192.168.1.20', 1, '2026-02-10 14:00:00'),
        (1, 'admin', '报告', '生成报告', 'POST', '/api/reports', '192.168.1.10', 1, '2026-02-28 16:00:00'),
        (1, 'admin', '检测', '新建检测任务', 'POST', '/api/detection/scan', '192.168.1.10', 1, '2026-04-04 09:12:00'),
        (2, 'security', '告警', '处置告警', 'PUT', '/api/alerts/16/handle', '192.168.1.20', 1, '2026-04-21 09:00:00'),
        (1, 'admin', '隔离', '删除隔离文件', 'DELETE', '/api/quarantine/6', '192.168.1.10', 1, '2026-02-09 10:00:00'),
        (3, 'zhangsan', '检测', '查看任务', 'GET', '/api/detection/tasks', '192.168.1.30', 1, '2026-04-15 10:00:00'),
        (4, 'lisi', '认证', '登录', 'POST', '/api/auth/login', '192.168.1.40', 1, '2026-04-12 11:30:00'),
        (5, 'wangwu', '检测', '新建检测任务', 'POST', '/api/detection/scan', '192.168.1.50', 1, '2026-02-03 14:23:00'),
        (1, 'admin', '系统', '修改菜单', 'PUT', '/api/system/menus/13', '192.168.1.10', 1, '2026-05-01 10:00:00'),
    ]
    cur.executemany("INSERT INTO sys_log (user_id, username, module, operation, method, url, ip, status, create_time) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)", logs)
    cur.close()
    print("part5 完成")
