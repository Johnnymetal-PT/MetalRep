import json

with open('.pg/projects/odoo-waterdetails-virgin-details-lda/tasks/tasks.json', 'r', encoding='utf-8') as f:
    tasks_data = json.load(f)

with open('.pg/projects/odoo-waterdetails-virgin-details-lda/chatter/chatter.json', 'r', encoding='utf-8') as f:
    chatter_data = json.load(f)

with open('.pg/projects/odoo-waterdetails-virgin-details-lda/attachments/attachments.json', 'r', encoding='utf-8') as f:
    attachments_data = json.load(f)

tasks = tasks_data.get('tasks', [])

target_ids = [7038, 7422, 7423, 7350, 7258, 7257] # let's check recent task ids

# print recent 10 tasks in detail
for t in tasks[-10:]:
    tid = t.get('odoo_id')
    print(f"\n==================== TASK ID: {tid} - {t.get('name')} ====================")
    print(f"Stage: {t.get('stage_name')} | Closed: {t.get('is_closed')}")
    print(f"Description HTML:\n{t.get('description')}")
    
    # Check chatter for this task
    task_chatter = [c for c in chatter_data.get('messages', []) if c.get('res_id') == tid and c.get('model') == 'project.task']
    if task_chatter:
        print("\n--- Chatter ---")
        for c in task_chatter:
            print(f"[{c.get('date')}] {c.get('author_name')}: {c.get('body')}")
            
    # Check attachments for this task
    task_att = [a for a in attachments_data.get('attachments', []) if a.get('res_id') == tid and a.get('res_model') == 'project.task']
    if task_att:
        print("\n--- Attachments ---")
        for a in task_att:
            print(f"- {a.get('name')} (id: {a.get('id')}, url: {a.get('url')})")
