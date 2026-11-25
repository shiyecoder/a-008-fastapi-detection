"""种子数据 part1: 用户/角色/菜单（匹配 ORM 字段）"""

def seed_users_roles_menus(conn):
    cur = conn.cursor()

    # sys_user(id, username, password, nickname, email, phone, avatar, status, remark, create_time, update_time)
    users = [
        (1, 'admin', 'PLACEHOLDER', '超级管理员', 'admin@webshell.com', '13800000001', None, 1, '系统管理员账号'),
        (2, 'security', 'PLACEHOLDER', '安全经理', 'security@webshell.com', '13800000002', None, 1, '安全运营负责人'),
        (3, 'zhangsan', 'PLACEHOLDER', '张三', 'zhangsan@webshell.com', '13800000003', None, 1, ''),
        (4, 'lisi', 'PLACEHOLDER', '李四', 'lisi@webshell.com', '13800000004', None, 1, ''),
        (5, 'wangwu', 'PLACEHOLDER', '王五', 'wangwu@webshell.com', '13800000005', None, 1, ''),
        (6, 'zhaoliu', 'PLACEHOLDER', '赵六', 'zhaoliu@webshell.com', '13800000006', None, 1, ''),
        (7, 'sunqi', 'PLACEHOLDER', '孙七', 'sunqi@webshell.com', '13800000007', None, 1, ''),
        (8, 'zhouba', 'PLACEHOLDER', '周八', 'zhouba@webshell.com', '13800000008', None, 0, '已禁用账号'),
        (9, 'wujiu', 'PLACEHOLDER', '吴九', 'wujiu@webshell.com', '13800000009', None, 1, ''),
        (10, 'zhengshi', 'PLACEHOLDER', '郑十', 'zhengshi@webshell.com', '13800000010', None, 1, ''),
    ]
    cur.executemany("INSERT INTO sys_user (id, username, password, nickname, email, phone, avatar, status, remark) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)", users)

    # sys_role(id, role_name, role_code, status, remark)
    roles = [
        (1, '超级管理员', 'admin', 1, '系统最高权限'),
        (2, '安全经理', 'security', 1, '安全运营管理'),
        (3, '普通用户', 'user', 1, '普通操作用户'),
    ]
    cur.executemany("INSERT INTO sys_role (id, role_name, role_code, status, remark) VALUES (%s,%s,%s,%s,%s)", roles)

    # sys_menu(id, parent_id, name, path, component, icon, sort, menu_type, perms, visible)
    # menu_type: 1=菜单 2=按钮（catalog 也用 1）
    menus = [
        (1, 0, '工作台', '/dashboard', 'dashboard/index', 'DataLine', 1, 1, 'dashboard', 1),
        (10, 0, 'Webshell检测', '/detection', '', 'Aim', 10, 1, '', 1),
        (11, 10, '检测扫描', '/detection/scan', 'detection/Scan', 'Search', 1, 1, 'detection:scan', 1),
        (12, 10, '检测任务', '/detection/list', 'detection/List', 'Document', 2, 1, 'detection:list', 1),
        (13, 10, 'YARA规则', '/detection/yara', 'detection/Yara', 'Files', 3, 1, 'detection:yara', 1),
        (14, 10, '隔离区', '/detection/quarantine', 'detection/Quarantine', 'Lock', 4, 1, 'detection:quarantine', 1),
        (40, 0, '告警中心', '/alert', '', 'BellFilled', 40, 1, '', 1),
        (41, 40, '告警列表', '/alert/list', 'alert/List', 'Warning', 1, 1, 'alert:list', 1),
        (42, 40, '漏洞修复库', '/alert/vuln-fix', 'alert/VulnFix', 'Tools', 2, 1, 'alert:vuln-fix', 1),
        (50, 0, '报告管理', '/report', '', 'DocumentChecked', 50, 1, '', 1),
        (51, 50, '报告列表', '/report/list', 'report/List', 'Files', 1, 1, 'report:list', 1),
        (60, 0, '系统管理', '/system', '', 'Setting', 60, 1, '', 1),
        (61, 60, '用户管理', '/system/user', 'system/User', 'User', 1, 1, 'system:user', 1),
        (62, 60, '角色管理', '/system/role', 'system/Role', 'UserFilled', 2, 1, 'system:role', 1),
        (63, 60, '菜单管理', '/system/menu', 'system/Menu', 'Menu', 3, 1, 'system:menu', 0),  # visible=0 隐藏
        (64, 60, '操作日志', '/system/log', 'system/Log', 'Document', 4, 1, 'system:log', 1),
    ]
    cur.executemany("INSERT INTO sys_menu (id, parent_id, name, path, component, icon, sort, menu_type, perms, visible) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", menus)

    # sys_user_role(user_id, role_id)
    user_roles = [(1, 1), (2, 2), (3, 3), (4, 3), (5, 3), (6, 3), (7, 3), (8, 3), (9, 3), (10, 3)]
    cur.executemany("INSERT INTO sys_user_role (user_id, role_id) VALUES (%s, %s)", user_roles)

    # sys_role_menu
    role_menus = []
    for mid in [m[0] for m in menus]:
        role_menus.append((1, mid))
    for mid in [1, 10, 11, 12, 13, 14, 40, 41, 42, 50, 51]:
        role_menus.append((2, mid))
    for mid in [1, 10, 11, 12, 14, 40, 41]:
        role_menus.append((3, mid))
    cur.executemany("INSERT INTO sys_role_menu (role_id, menu_id) VALUES (%s, %s)", role_menus)
    cur.close()
    print("part1 完成")
