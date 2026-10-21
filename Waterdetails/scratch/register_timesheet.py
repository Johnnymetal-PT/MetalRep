import json, urllib.request

pg = json.load(open('.pg_framework/credentials/brodoo_credentials.json'))
def rpc(u, s, m, args):
    data = json.dumps({'jsonrpc': '2.0', 'method': 'call', 'params': {'service': s, 'method': m, 'args': args}}).encode('utf-8')
    req = urllib.request.Request(u.rstrip('/') + '/jsonrpc', data=data, headers={'Content-Type': 'application/json; charset=utf-8'})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))['result']

uid = rpc(pg['url'], 'common', 'authenticate', [pg['db'], pg['login'], pg['api_key'], {}])

vals = {
    'name': 'Análise técnica do erro de validação no ficheiro SAF-T de Agosto (ProductGroup vazio), identificação dos artigos sem categoria associada na base de dados e elaboração de resposta com links diretos para regularização.',
    'project_id': 261,
    'task_id': 7268,
    'user_id': 80,
    'employee_id': 35,
    'unit_amount': 0.25,
    'date': '2026-08-31',
}

res = rpc(pg['url'], 'object', 'execute_kw', [pg['db'], uid, pg['api_key'], 'account.analytic.line', 'create', [vals]])
print('Timesheet created successfully! ID:', res)
