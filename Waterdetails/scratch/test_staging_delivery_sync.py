import json
import os
import urllib.request

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
conn = jsonrpc_call(
    pg_cred["url"], "object", "execute_kw",
    [
        pg_cred["db"], pg_uid, pg_cred["api_key"],
        "pg.odoo.connection", "search_read",
        [[["id", "=", 11]]],
        {"fields": ["id", "name", "purpose", "base_url", "database", "login", "api_key"]}
    ]
)[0]

target_url = conn["base_url"]
target_db = conn["database"]
target_login = conn["login"]
target_key = conn["api_key"]

uid = jsonrpc_call(target_url, "common", "authenticate", [target_db, target_login, target_key, {}])
print(f"Staging auth uid: {uid}")

# Check module version
modules = jsonrpc_call(
    target_url, "object", "execute_kw",
    [target_db, uid, target_key, "ir.module.module", "search_read", [[["name", "=", "pg_stock_delivery_address"]]], {"fields": ["id", "name", "state", "installed_version", "latest_version"]}]
)
print(f"Module state in staging: {modules}")

# Upgrade module in staging if needed
if modules:
    mod_id = modules[0]["id"]
    print(f"Triggering button_immediate_upgrade for module {mod_id}...")
    jsonrpc_call(target_url, "object", "execute_kw", [target_db, uid, target_key, "ir.module.module", "button_immediate_upgrade", [[mod_id]]])
    print("Module upgraded successfully!")

# Re-check module version
modules = jsonrpc_call(
    target_url, "object", "execute_kw",
    [target_db, uid, target_key, "ir.module.module", "search_read", [[["name", "=", "pg_stock_delivery_address"]]], {"fields": ["id", "name", "state", "installed_version", "latest_version"]}]
)
print(f"Module state after upgrade: {modules}")

# Find an outgoing picking type in company 2 (Starplast)
picking_types = jsonrpc_call(
    target_url, "object", "execute_kw",
    [target_db, uid, target_key, "stock.picking.type", "search_read", [[["code", "=", "outgoing"]]], {"fields": ["id", "name", "company_id", "default_location_src_id", "default_location_dest_id"]}]
)
print(f"Outgoing picking types: {picking_types[:2]}")
ptype = picking_types[0]

# Create a test picking with partner 50189 (HIDRO INSTALL) in Starplast
picking_vals = {
    "partner_id": 50189,
    "picking_type_id": ptype["id"],
    "location_id": ptype["default_location_src_id"][0],
    "location_dest_id": ptype["default_location_dest_id"][0],
    "pg_delivery_street": "Avenida de Teste Staging 999",
    "pg_delivery_city": "Tomar",
    "pg_delivery_zip": "2300-001",
}

print("Creating test picking in staging...")
picking_id = jsonrpc_call(
    target_url, "object", "execute_kw",
    [target_db, uid, target_key, "stock.picking", "create", [picking_vals]]
)
print(f"Test picking created: {picking_id}")

# Read created picking
picking_data = jsonrpc_call(
    target_url, "object", "execute_kw",
    [target_db, uid, target_key, "stock.picking", "search_read", [[["id", "=", picking_id]]], {"fields": ["id", "partner_id", "pg_delivery_address_id", "company_id"]}]
)[0]
print(f"Picking data: {picking_data}")

created_addr_id = picking_data["pg_delivery_address_id"][0]
addr_data = jsonrpc_call(
    target_url, "object", "execute_kw",
    [target_db, uid, target_key, "res.partner", "search_read", [[["id", "=", created_addr_id]]], {"fields": ["id", "name", "company_id", "parent_id", "type", "pg_picking_delivery_address"]}]
)[0]
print(f"Created delivery address data: {addr_data}")

# Assertions
assert addr_data["company_id"] is False, f"Expected company_id False but got {addr_data['company_id']}"
assert addr_data["parent_id"][0] == 50189, f"Expected parent_id 50189 but got {addr_data['parent_id']}"
assert addr_data["type"] == "delivery", f"Expected type delivery but got {addr_data['type']}"
print("\n>>> VALIDATION SUCCESSFUL: Delivery address created with company_id=False and root parent_id! <<<")

# Cleanup test records
print("Cleaning up test records...")
jsonrpc_call(target_url, "object", "execute_kw", [target_db, uid, target_key, "stock.picking", "unlink", [[picking_id]]])
jsonrpc_call(target_url, "object", "execute_kw", [target_db, uid, target_key, "res.partner", "unlink", [[created_addr_id]]])
print("Test records cleaned up successfully.")
