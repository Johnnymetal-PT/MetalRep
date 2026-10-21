"""Read-only storage audit against production (DST) via JSON-RPC. No writes."""
import os, json, urllib.request
from pathlib import Path

env = Path(__file__).with_name(".promote.env")
for raw in env.read_text(encoding="utf-8").splitlines():
    line = raw.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

URL = os.environ["DST_URL"].rstrip("/")
DB = os.environ["DST_DB"]; LOGIN = os.environ["DST_LOGIN"]; KEY = os.environ["DST_API_KEY"]
GB = 1024**3; MB = 1024**2

_id = [0]
def jsonrpc(service, method, args):
    _id[0] += 1
    payload = {"jsonrpc": "2.0", "method": "call",
               "params": {"service": service, "method": method, "args": args}, "id": _id[0]}
    req = urllib.request.Request(f"{URL}/jsonrpc", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        res = json.loads(r.read())
    if "error" in res:
        raise RuntimeError(json.dumps(res["error"].get("data", res["error"]), indent=2)[:800])
    return res["result"]

UID = jsonrpc("common", "authenticate", [DB, LOGIN, KEY, {}])
print(f"[DST] uid={UID}  server={jsonrpc('common','version',[]).get('server_version')}\n")

def call(model, method, args, kw=None):
    return jsonrpc("object", "execute_kw", [DB, UID, KEY, model, method, args, kw or {}])

def rg(domain, groupby, fields=("file_size:sum",), lazy=False, ctx=None):
    kw = {"lazy": lazy}
    if ctx: kw["context"] = ctx
    return call("ir.attachment", "read_group", [domain, list(fields), list(groupby)], kw)

PT = {"janeiro":1,"fevereiro":2,"março":3,"marco":4-1,"abril":4,"maio":5,"junho":6,
      "julho":7,"agosto":8,"setembro":9,"outubro":10,"novembro":11,"dezembro":12}
def mkey(label):
    if not label: return (9999,99)
    parts = label.lower().replace("março","março").split()
    mon = PT.get(parts[0], 99); yr = int(parts[-1])
    return (yr, mon)

def monthly(domain, title):
    rows = rg(domain, ["create_date:month"])
    rows.sort(key=lambda r: mkey(r.get("create_date:month")))
    print(f"=== {title} ===")
    cum = 0
    for r in rows:
        sz = r.get("file_size") or 0; cum += sz
        print(f"  {str(r.get('create_date:month')):16} +{sz/MB:9.1f} MB  ({r['__count']:>6,})  cum={cum/GB:6.3f} GB")
    print()
    return rows

# A) Visible attachments (res_field = False -> uploaded files)
tot = rg([], [])[0]
print(f"VISIBLE attachments (uploaded files, res_field=False): count={tot['__count']:,}  {(tot['file_size'] or 0)/GB:.2f} GB")

# B) Field-store attachments (res_field set -> product images etc.), needs explicit res_field domain
try:
    fld = rg([("res_field", "!=", False)], [])[0]
    print(f"FIELD-STORE attachments (res_field set, e.g. product images): count={fld['__count']:,}  {(fld['file_size'] or 0)/GB:.2f} GB")
    print("\n--- Field-store by res_model (top 10) ---")
    fm = [r for r in rg([("res_field","!=",False)], ["res_model"]) if r.get("file_size")]
    fm.sort(key=lambda r: -(r["file_size"] or 0))
    for r in fm[:10]:
        print(f"  {str(r.get('res_model')):28} count={r['__count']:>8,}  {r['file_size']/GB:8.3f} GB")
except Exception as e:
    print("FIELD-STORE query failed:", e)
print()

print("--- Visible by res_model (top 12) ---")
bm = [r for r in rg([], ["res_model"]) if r.get("file_size")]
bm.sort(key=lambda r: -(r["file_size"] or 0))
for r in bm[:12]:
    print(f"  {str(r.get('res_model')):28} count={r['__count']:>8,}  {r['file_size']/GB:8.3f} GB")
print()

monthly([("res_model", "=", "discuss.channel")], "DISCUSS growth by month")
# Organic recurring = exclude one-off/technical: product.*, ir.ui.view (web assets), website
organic = ["&","&","&",
           ("res_model","not in",["product.template","product.product","product.image"]),
           ("res_model","!=","ir.ui.view"),
           ("res_model","!=","website"),
           ("res_model","!=","documents.document")]
monthly(organic, "ORGANIC recurring growth (excl. product/*, ir.ui.view, website, documents)")
