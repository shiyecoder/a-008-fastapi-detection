import urllib.request, urllib.error, json

TOK = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOjEsInVzZXJuYW1lIjoiYWRtaW4iLCJleHAiOjE3Nzk0MzcxNTd9.sKu4YFpfsf1KHMX_uPo_YvxyWqcXu1wPi7eWZNhPMsE'

def G(p):
    try:
        r = urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8080'+p, headers={'Authorization':'Bearer '+TOK}))
        body = r.read().decode()
        j = json.loads(body)
        d = j.get('data')
        if isinstance(d, dict):
            n = 'list='+str(len(d.get('list',[]))) if 'list' in d else 'keys='+','.join(list(d.keys())[:6])
        elif isinstance(d, list):
            n = 'len='+str(len(d))
        else:
            n = '-'
        print(f"{p:55s} code={j.get('code')} {n}")
    except urllib.error.HTTPError as e:
        print(p, 'HTTP', e.code, e.read().decode()[:200])
    except Exception as e:
        print(p, 'ERR', e)

for p in [
    '/api/auth/info',
    '/api/user/page?page=1&size=5',
    '/api/role/page?page=1&size=5',
    '/api/role/all',
    '/api/menu/tree',
    '/api/log/page?page=1&size=5',
    '/api/detection/page?page=1&size=5',
    '/api/yara/page?page=1&size=5',
    '/api/quarantine/page?page=1&size=5',
    '/api/alert/page?page=1&size=5',
    '/api/vuln-fix/page?page=1&size=5',
    '/api/report/page?page=1&size=5',
    '/api/dashboard/overview',
    '/api/dashboard/trend',
    '/api/dashboard/risk-level',
    '/api/dashboard/detect-type',
    '/api/dashboard/lang-distribution',
    '/api/dashboard/alert-status',
]:
    G(p)
