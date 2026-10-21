import xmlrpc.client, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

URL     = 'https://parametroglobal.odoo.com'
DB      = 'parametro-main-29950773'
LOGIN   = 'pedro.coelho@parametro.global'
API_KEY = '9e000dc8997ff1c2f3afe4920138dfe03ffe6973'

WRONG_PROJECT = 126
RIGHT_PROJECT = 93
TASK_IDS      = list(range(5670, 5707))  # 5670–5706

common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common', allow_none=True)
uid    = common.authenticate(DB, LOGIN, API_KEY, {})
print(f'Authenticated: uid={uid}')

models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object', allow_none=True)

def exe(model, method, args, kw=None):
    return models.execute_kw(DB, uid, API_KEY, model, method, args, kw or {})

# 1) Confirmar projecto destino
proj = exe('project.project', 'read', [[RIGHT_PROJECT]], {'fields': ['name', 'date_start', 'date']})
print(f'Target project: {proj[0]["name"]} (id={RIGHT_PROJECT})')

# 2) Ler stages do projecto destino
stages = exe('project.task.type', 'search_read',
    [[['project_ids', 'in', [RIGHT_PROJECT]]]],
    {'fields': ['id', 'name', 'sequence'], 'order': 'sequence asc'})
print('Stages in target project:')
for s in stages:
    print(f'  [{s["id"]}] seq={s["sequence"]} {s["name"]}')

# Mapear sprint vs backlog (mesmo critério)
from datetime import date as _date
KW_SPRINT  = ('sprint', 'progresso', 'curso', 'doing', 'in progress', 'ativo', 'in_progress')
KW_BACKLOG = ('backlog', 'todo', 'a fazer', 'new', 'novo', 'incoming')

stage_sprint  = next((s['id'] for s in stages if any(k in s['name'].lower() for k in KW_SPRINT)),  None)
stage_backlog = next((s['id'] for s in stages if any(k in s['name'].lower() for k in KW_BACKLOG)), None)
if stage_sprint  is None and stages: stage_sprint  = stages[0]['id']
if stage_backlog is None and stages: stage_backlog = stages[1]['id'] if len(stages) > 1 else stages[0]['id']

sprint_name  = next((s['name'] for s in stages if s['id'] == stage_sprint),  '?')
backlog_name = next((s['name'] for s in stages if s['id'] == stage_backlog), '?')
print(f'Sprint stage  -> [{stage_sprint}] {sprint_name}')
print(f'Backlog stage -> [{stage_backlog}] {backlog_name}')

SPRINT_CUTOFF = _date(2026, 6, 15)

# 3) Ler as tarefas criadas (verificar que existem e estão no projecto errado)
tasks = exe('project.task', 'search_read',
    [[['id', 'in', TASK_IDS]]],
    {'fields': ['id', 'name', 'project_id', 'date_deadline']})
print(f'\nFound {len(tasks)} tasks to move')

# 4) Mover cada tarefa para o projecto correcto + corrigir stage
moved = 0
errors = 0
for t in tasks:
    try:
        deadline_str = (t.get('date_deadline') or '2026-12-31')[:10]
        d = _date.fromisoformat(deadline_str)
        new_stage = stage_sprint if d <= SPRINT_CUTOFF else stage_backlog
        exe('project.task', 'write', [[t['id']], {
            'project_id': RIGHT_PROJECT,
            'stage_id':   new_stage,
        }])
        print(f'  ✓ [{t["id"]}] moved -> project={RIGHT_PROJECT} stage={new_stage}')
        moved += 1
    except Exception as e:
        print(f'  ✗ [{t["id"]}] error: {e}')
        errors += 1

# 5) Actualizar datas do projecto correcto
print(f'\nUpdating project {RIGHT_PROJECT} dates (2026-05-25 -> 2027-01-31) ...')
exe('project.project', 'write', [[RIGHT_PROJECT], {
    'date_start': '2026-05-25',
    'date':       '2027-01-31',
}])
print('  Project dates updated.')

# 6) Reverter datas do projecto errado (restaurar sem datas)
print(f'Reverting dates on wrong project {WRONG_PROJECT} ...')
exe('project.project', 'write', [[WRONG_PROJECT], {
    'date_start': False,
    'date':       False,
}])
print('  Reverted.')

print(f'\n{"="*50}')
print(f'DONE — {moved} tasks moved, {errors} errors')
print(f'{"="*50}')
