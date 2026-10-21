import urllib.request, http.cookiejar, json, sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

URL   = 'https://parametroglobal.odoo.com'
LOGIN = 'pedro.coelho@parametro.global'
KEY   = '9e000dc8997ff1c2f3afe4920138dfe03ffe6973'

# 1) Obter session_id inicial via GET /web
jar    = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

req0 = urllib.request.Request(URL + '/web', headers={'User-Agent': 'Mozilla/5.0'})
with opener.open(req0, timeout=15) as r:
    pass

session_id = next((c.value for c in jar if c.name == 'session_id'), None)
print(f'Initial session_id: {session_id[:30] if session_id else None}')

# 2) POST /web/session/authenticate COM o session cookie
# (o proxy deve saber a BD pelo hostname da sessao)
payload = json.dumps({
    'jsonrpc': '2.0', 'method': 'call', 'id': 1,
    'params': {'db': 'parametroglobal', 'login': LOGIN, 'password': KEY},
}).encode()
req1 = urllib.request.Request(
    URL + '/web/session/authenticate',
    data=payload,
    headers={
        'Content-Type': 'application/json',
        'Cookie': f'session_id={session_id}' if session_id else '',
        'X-Odoo-Dbname': 'parametroglobal',
    },
)
try:
    with opener.open(req1, timeout=15) as r:
        data = json.loads(r.read())
    result = data.get('result') or {}
    error  = (data.get('error') or {}).get('data', {})
    print(f'Authenticate result: uid={result.get("uid")} db={result.get("db")} name={result.get("name")}')
    if error:
        print(f'Error: {error.get("message","?")}')
    # listar todos os campos do result
    for k, v in result.items():
        print(f'  {k}: {str(v)[:80]}')
except Exception as e:
    print(f'Error: {e}')

# 3) Tentar /web/session/get_session_info com o cookie da sessao autenticada
print('\n--- get_session_info after cookies ---')
payload2 = json.dumps({'jsonrpc': '2.0', 'method': 'call', 'id': 2, 'params': {}}).encode()
req2 = urllib.request.Request(
    URL + '/web/session/get_session_info',
    data=payload2,
    headers={'Content-Type': 'application/json'},
)
try:
    with opener.open(req2, timeout=15) as r:
        data2 = json.loads(r.read())
    result2 = data2.get('result') or {}
    for k, v in result2.items():
        print(f'  {k}: {str(v)[:100]}')
except Exception as e:
    print(f'Error: {e}')
