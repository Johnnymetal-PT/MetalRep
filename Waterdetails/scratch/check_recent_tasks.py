import json

with open('.pg/projects/odoo-waterdetails-virgin-details-lda/tasks/tasks.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

tasks = data.get('tasks', [])

print(f"Total tasks: {len(tasks)}")

for i in range(len(tasks) - 15, len(tasks)):
    t = tasks[i]
    print(f"\n==================== TASK [{i}] ====================")
    print(f"Name: {t.get('name')}")
    print(f"Stage: {t.get('stage_name')}")
    print(f"Scope state: {t.get('scope_state')}")
    print(f"Closed: {t.get('is_closed')} | Cancelled: {t.get('is_cancelled')}")
    print(f"Description:\n{t.get('description_text') or t.get('description')}")
