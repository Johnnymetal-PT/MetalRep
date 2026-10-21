import json

with open('.pg/projects/odoo-waterdetails-virgin-details-lda/tasks/tasks.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for t in data.get('tasks', []):
    if t.get('odoo_id') in [7038, 7422, 7423]:
        print(f"=== TASK {t.get('odoo_id')}: {t.get('name')} ===")
        print("DESCRIPTION HTML:")
        print(t.get('description'))
        print("\n" + "="*50 + "\n")
