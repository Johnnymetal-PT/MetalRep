import xmlrpc.client, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

URL   = 'https://parametroglobal.odoo.com'
DB    = 'parametro-main-29950773'
LOGIN = 'pedro.coelho@parametro.global'
KEY   = '9e000dc8997ff1c2f3afe4920138dfe03ffe6973'

common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common', allow_none=True)
uid    = common.authenticate(DB, LOGIN, KEY, {})
models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object', allow_none=True)

def exe(model, method, args, kw=None):
    return models.execute_kw(DB, uid, KEY, model, method, args, kw or {})

# campos de horas disponíveis
all_fields = exe('project.task', 'fields_get', [], {'attributes': ['string', 'type']})
hour_fields = {k: v for k, v in all_fields.items()
               if any(x in k.lower() for x in ['hour', 'alloc', 'planned'])}
print('Hour-related fields on project.task:')
for k, v in sorted(hour_fields.items()):
    print(f'  {k} ({v["type"]}) — {v["string"]}')

# ler as tarefas
tasks = exe('project.task', 'read', [list(range(5670, 5707))],
            {'fields': ['id', 'name', 'allocated_hours', 'milestone_id']})

print(f'\n{"Task":<70} {"allocated_hours":>16}')
print('-' * 88)
total = 0
for t in sorted(tasks, key=lambda x: x['id']):
    h = t.get('allocated_hours') or 0
    total += h
    name = t['name'][:68]
    print(f'  [{t["id"]}] {name:<66} {h:>12.1f}h')

print('-' * 88)
print(f'  {"TOTAL":<70} {total:>12.1f}h')
if total > 0:
    print(f'  (= {total/8:.1f} dias / {total/168:.1f} meses a 8h/dia)')
else:
    print('  --> Nenhuma hora alocada nas tarefas (campo allocated_hours = 0 em todas)')
