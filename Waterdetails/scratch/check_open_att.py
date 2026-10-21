import json

with open('.pg/projects/odoo-waterdetails-virgin-details-lda/attachments/attachments.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for a in data.get('attachments', []):
    if a.get('res_id') in [7038, 7422, 7423]:
        print(f"Task {a.get('res_id')}: {a.get('name')} | mimetype: {a.get('mimetype')} | url: {a.get('url')} | desc: {a.get('description')}")
