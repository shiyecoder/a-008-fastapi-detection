"""种子数据 part2: YARA规则 + 漏洞修复库（匹配 ORM）"""

def seed_yara_vuln(conn):
    cur = conn.cursor()

    # yara_rule(rule_name, language, severity, pattern, description, enabled)
    yara_rules = [
        ('PHP_Eval_Webshell', 'php', 'high', r'eval\s*\(.*\$_(GET|POST|REQUEST)', 'PHP eval+用户输入：典型一句话木马', 1),
        ('PHP_System_Cmd', 'php', 'high', r'(system|exec|passthru|shell_exec)\s*\(.*\$_', 'PHP命令执行函数+用户输入', 1),
        ('PHP_Assert_Backdoor', 'php', 'high', r'assert\s*\(\s*\$_(GET|POST|REQUEST)', 'PHP assert后门', 1),
        ('PHP_Base64_Decode_Eval', 'php', 'high', r'eval\s*\(\s*base64_decode', 'PHP混淆Webshell（base64+eval）', 1),
        ('JSP_Runtime_Exec', 'jsp', 'high', r'Runtime\.getRuntime\(\)\.exec', 'JSP执行系统命令', 1),
        ('JSP_Class_Loader', 'jsp', 'medium', r'defineClass|ClassLoader', 'JSP类加载（可能动态加载木马）', 1),
        ('ASP_Eval', 'asp', 'high', r'execute\s*\(\s*request', 'ASP execute+request 一句话', 1),
        ('Python_Eval_Input', 'python', 'high', r'(eval|exec)\s*\(.*request\.', 'Python eval/exec+request参数', 1),
        ('Java_Reflection_Exec', 'java', 'medium', r'getRuntime\(\)\.exec\(.*request\.', 'Java反射执行命令', 1),
        ('PHP_Preg_Replace_e', 'php', 'high', r'preg_replace\s*\(.+/e', 'preg_replace e修饰符代码执行', 1),
        ('PHP_Create_Function', 'php', 'medium', r'create_function\s*\(', 'PHP create_function后门', 0),
    ]
    cur.executemany("INSERT INTO yara_rule (rule_name, language, severity, pattern, description, enabled) VALUES (%s,%s,%s,%s,%s,%s)", yara_rules)

    # vuln_fix_mapping(vuln_type[unique], severity, description, fix_advice, patch_url, reference)
    vuln_fix = [
        ('SQL注入', 'high', 'SQL注入是攻击者通过控制SQL语句执行恶意操作', '使用参数化查询/预编译语句；对输入进行白名单校验；使用ORM框架', 'https://owasp.org/www-community/attacks/SQL_Injection', 'OWASP Top 10 - A03:2021'),
        ('反射型XSS', 'medium', '攻击者构造URL，受害者点击后执行恶意脚本', '对所有输出进行HTML转义；使用CSP；对输入做白名单过滤', 'https://owasp.org/www-community/attacks/xss/', 'OWASP Top 10 - A03:2021'),
        ('存储型XSS', 'high', '恶意脚本存入服务端，所有访问者均会执行', '后端入库前严格过滤；输出时HTML实体化；CSP限制脚本来源', 'https://owasp.org/www-community/attacks/xss/', 'OWASP Top 10 - A03:2021'),
        ('CSRF', 'medium', '攻击者诱导用户访问构造好的页面执行恶意操作', '使用CSRF Token；SameSite Cookie；关键操作二次验证', 'https://owasp.org/www-community/attacks/csrf', 'OWASP A01:2021'),
        ('文件上传漏洞', 'high', '攻击者上传Webshell等恶意文件', '严格白名单后缀；检查MIME；重命名；存储到非Web目录；禁止脚本执行', 'https://owasp.org/www-community/vulnerabilities/Unrestricted_File_Upload', 'CWE-434'),
        ('命令注入', 'high', '通过控制系统命令参数执行恶意命令', '禁用system/exec等危险函数；使用参数化API；白名单过滤', 'https://owasp.org/www-community/attacks/Command_Injection', 'CWE-77'),
        ('目录遍历', 'medium', '通过../访问Web根目录外的文件', '规范化路径并校验是否在允许目录内；禁止用户控制文件路径', 'https://owasp.org/www-community/attacks/Path_Traversal', 'CWE-22'),
        ('弱口令', 'medium', '使用admin/123456等弱密码', '强制密码复杂度；启用MFA；登录失败锁定；定期改密', 'https://owasp.org/www-community/attacks/Brute_force_attack', 'OWASP A07:2021'),
        ('信息泄露', 'low', '错误页/调试信息暴露敏感数据', '关闭调试模式；统一错误处理；移除版本banner', 'https://owasp.org/www-community/Improper_Error_Handling', 'CWE-209'),
        ('Webshell后门', 'high', '攻击者上传一句话/大马用于持续控制', '定期扫描上传目录；禁用危险函数；最小化Web运行权限；WAF', 'https://owasp.org/www-community/attacks/', 'CWE-78'),
    ]
    cur.executemany("INSERT INTO vuln_fix_mapping (vuln_type, severity, description, fix_advice, patch_url, reference) VALUES (%s,%s,%s,%s,%s,%s)", vuln_fix)
    cur.close()
    print("part2 完成")
