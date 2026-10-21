import json

# Check both attachments files
for p in ['.pg/attachments/attachments.json', '.pg/projects/odoo-waterdetails-virgin-details-lda/attachments/attachments.json']:
    try:
        with open(p, 'r', encoding='utf-8') as f:
            data = json.load(f)
            atts = data.get('attachments', [])
            print(f"{p}: {len(atts)} attachments")
            for a in atts:
                res_id = a.get('res_id')
                if res_id in [7422, 7423, 7484, 7268, 7038, 7194, 7191, 7168, 7166, 7165, 7164]:
                    print(f"  res_id={res_id} | name={a.get('name')} | mimetype={a.get('mimetype')} | desc={a.get('description')} | url={a.get('url')}")
    except Exception as e:
        print(f"Error {p}: {e}")
