import json

with open('.pg/projects/odoo-waterdetails-virgin-details-lda/tasks/tasks.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

tasks = data.get('tasks', [])

print("=== ALL OPEN / NON-CLOSED TASKS ===")
open_tasks = []
for t in tasks:
    # Check if task is open
    if not t.get('is_closed') and not t.get('is_cancelled') and t.get('stage_name') not in ['Sprint Complete', 'Cancelado', 'Done']:
        open_tasks.append(t)

print(f"Found {len(open_tasks)} open tasks:")
for t in open_tasks:
    print(f"\nID: {t.get('odoo_id')} | Name: {t.get('name')} | Stage: {t.get('stage_name')}")
    print(f"Scope state: {t.get('scope_state')} | Track: {t.get('scope_track')}")
    print(f"Assignees: {t.get('assignees')}")
    desc = t.get('description_text') or t.get('description') or ''
    print(f"Description:\n{desc.strip()}")
