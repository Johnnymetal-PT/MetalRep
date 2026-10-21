import json
import os
import urllib.request

# 1. Read Brodoo PG credentials
base_dir = r"c:\Projetos\Waterdetails"
cred_path = os.path.join(base_dir, ".pg_framework", "credentials", "brodoo_credentials.json")
if not os.path.exists(cred_path):
    cred_path = os.path.join(base_dir, "..", "_pg_template", "credentials", "brodoo_credentials.json")

with open(cred_path, "r", encoding="utf-8") as f:
    pg_cred = json.load(f)

def jsonrpc_call(url, service, method, args):
    endpoint = url.rstrip("/") + "/jsonrpc"
    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "service": service,
            "method": method,
            "args": args
        }
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(endpoint, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        if "error" in res:
            raise Exception(f"Odoo error: {res['error']}")
        return res.get("result")

# Auth on PG Odoo
pg_uid = jsonrpc_call(pg_cred["url"], "common", "authenticate", [pg_cred["db"], pg_cred["login"], pg_cred["api_key"], {}])
print(f"PG Odoo auth successful, uid: {pg_uid}")

# Get client connections for project Waterdetails
conns = jsonrpc_call(
    pg_cred["url"], "object", "execute_kw",
    [
        pg_cred["db"], pg_uid, pg_cred["api_key"],
        "pg.odoo.connection", "search_read",
        [[["repository_id.name", "=", "Waterdetails"]]],
        {"fields": ["id", "name", "purpose", "base_url", "database", "login", "api_key"]}
    ]
)

print(f"Found {len(conns)} connections for Waterdetails:")
for c in conns:
    print(f" - {c['id']}: {c['name']} (purpose: {c['purpose']}, db: {c['database']}, url: {c['base_url']})")

for conn in conns:
    purpose = conn["purpose"]
    target_url = conn["base_url"]
    target_db = conn["database"]
    target_login = conn["login"]
    target_key = conn["api_key"] or pg_cred["api_key"]

    print(f"\n==========================================")
    print(f"Processing target: {purpose} ({target_url} / {target_db})")
    print(f"==========================================")

    try:
        target_uid = jsonrpc_call(target_url, "common", "authenticate", [target_db, target_login, target_key, {}])
        if not target_uid:
            print(f"Failed to authenticate to {target_url}")
            continue
        print(f"Authenticated to target Odoo, uid: {target_uid}")

        # 1. Get companies and their partner_ids
        companies = jsonrpc_call(
            target_url, "object", "execute_kw",
            [target_db, target_uid, target_key, "res.company", "search_read", [[]], {"fields": ["id", "name", "partner_id"]}]
        )
        company_partner_ids = set()
        for comp in companies:
            if comp.get("partner_id"):
                company_partner_ids.add(comp["partner_id"][0])
        print(f"Company partner IDs: {company_partner_ids}")

        # 2. Get users and their partner_ids (all active and inactive)
        users = jsonrpc_call(
            target_url, "object", "execute_kw",
            [target_db, target_uid, target_key, "res.users", "search_read", [["|", ["active", "=", True], ["active", "=", False]]], {"fields": ["id", "name", "partner_id"]}]
        )
        user_partner_ids = set()
        for u in users:
            if u.get("partner_id"):
                user_partner_ids.add(u["partner_id"][0])
        print(f"User partner IDs: {user_partner_ids}")

        protected_ids = company_partner_ids | user_partner_ids
        print(f"Total protected partner IDs: {len(protected_ids)}")

        # 3. Search all partners with company_id != False
        partners_with_company = jsonrpc_call(
            target_url, "object", "execute_kw",
            [
                target_db, target_uid, target_key, "res.partner", "search_read",
                [["|", ["active", "=", True], ["active", "=", False], ["company_id", "!=", False]]],
                {"fields": ["id", "name", "company_id", "type", "parent_id", "commercial_partner_id"]}
            ]
        )

        candidates = [p for p in partners_with_company if p["id"] not in protected_ids]
        print(f"Found {len(candidates)} partners with company_id != False (excluding protected):")
        for p in candidates:
            print(f"  ID {p['id']}: {p['name']} (Type: {p.get('type')}, Current Company: {p.get('company_id')}, Parent: {p.get('parent_id')})")

        if candidates:
            candidate_ids = [p["id"] for p in candidates]
            # Perform update
            print(f"Updating company_id = False for IDs: {candidate_ids}")
            res = jsonrpc_call(
                target_url, "object", "execute_kw",
                [target_db, target_uid, target_key, "res.partner", "write", [candidate_ids, {"company_id": False}]]
            )
            print(f"Write result: {res}")
        else:
            print("No candidate partners to update.")

    except Exception as e:
        print(f"Error on {purpose}: {e}")
