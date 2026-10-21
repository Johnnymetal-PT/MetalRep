import json, urllib.request

pg = json.load(open('.pg_framework/credentials/brodoo_credentials.json'))
def rpc(u, s, m, args):
    req = urllib.request.Request(u + '/jsonrpc', data=json.dumps({'jsonrpc': '2.0', 'method': 'call', 'params': {'service': s, 'method': m, 'args': args}}).encode(), headers={'Content-Type': 'application/json'})
    return json.loads(urllib.request.urlopen(req).read().decode())['result']

uid = rpc(pg['url'], 'common', 'authenticate', [pg['db'], pg['login'], pg['api_key'], {}])
conns = rpc(pg['url'], 'object', 'execute_kw', [pg['db'], uid, pg['api_key'], 'pg.odoo.connection', 'search_read', [[['id', '=', 12]]], {'fields': ['base_url', 'database', 'login', 'api_key']}])
prod_conn = conns[0]
target_url = prod_conn['base_url'].rstrip('/') + '/jsonrpc'
target_uid = rpc(target_url, 'common', 'authenticate', [prod_conn['database'], prod_conn['login'], prod_conn['api_key'], {}])

# Aug 2026 invoice lines
lines = rpc(target_url, 'object', 'execute_kw', [prod_conn['database'], target_uid, prod_conn['api_key'], 'account.move.line', 'search_read', [[['move_id.company_id', '=', 1], ['move_id.invoice_date', '>=', '2026-08-01'], ['move_id.invoice_date', '<=', '2026-08-31'], ['move_id.state', '=', 'posted'], ['move_id.move_type', 'in', ['out_invoice', 'out_refund']], ['display_type', '=', 'product']]], {'fields': ['product_id']}])
aug_prod_ids = set([l['product_id'][0] for l in lines if l['product_id']])

# All templates without categ_id
templates = rpc(target_url, 'object', 'execute_kw', [prod_conn['database'], target_uid, prod_conn['api_key'], 'product.template', 'search_read', [[['categ_id', '=', False]]], {'fields': ['id', 'name', 'default_code', 'type', 'product_variant_ids']}])

print('=== PRODUTOS FATURADOS EM AGOSTO (SEM CATEGORIA) ===')
for t in templates:
    if any(v in aug_prod_ids for v in t['product_variant_ids']):
        code = t['default_code'] or '-'
        print(f"- **{t['name']}** (Ref: `{code}`): https://virgin-details.odoo.com/web#id={t['id']}&model=product.template")

print('\n=== RESTANTES ARTIGOS NA BASE DE DADOS SEM CATEGORIA ===')
for t in templates:
    if not any(v in aug_prod_ids for v in t['product_variant_ids']):
        code = t['default_code'] or '-'
        print(f"- **{t['name']}** (Ref: `{code}`): https://virgin-details.odoo.com/web#id={t['id']}&model=product.template")
