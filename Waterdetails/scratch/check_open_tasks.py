import json

with open('.pg/projects/odoo-waterdetails-virgin-details-lda/tasks/tasks.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

tasks = data.get('tasks', [])

print("=== ALL NON-CLOSED / INCOMPLETE TASKS ===")
for i, t in enumerate(tasks):
    if not t.get('is_closed') or t.get('stage_name') in ['Backlog', 'Sprint Backlog', 'Sprint in Progress']:
        print(f"\n--- Task [{i}] | ID: {t.get('odoo_id')} | Name: {t.get('name')} | Stage: {t.get('stage_name')} | Closed: {t.get('is_closed')} ---")
        print(f"Description:\n{t.get('description_text') or t.get('description')}")
