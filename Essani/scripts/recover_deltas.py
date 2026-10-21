"""Recover Ana's manual edits from archived templates back into active templates.

What happened:
- Active templates in DST were promoted from Test (Backup state, ~10/05).
- Archived templates in DST hold the state Ana had built up between 10/05 and
  archive time (~22/05) -- in particular, default_code values she filled in or
  edited manually.
- This script transfers those deltas (currently: default_code on template and
  on variant) back to the active templates.

Matching:
- template-level: by name (exact). One archived <-> one active.
  If multiple archived share a name, use the most recently created (max id).
- variant-level: within the matched template pair, by ptav signature
  (attribute_name, value_name).

Conflict rules:
- active has no code, archived has code  ->  copy (RECOVER).
- active has code, archived has DIFFERENT code  ->  copy archived (Ana's value wins).
- active has code, archived has same code  ->  no-op.
- active has code, archived has no code  ->  no-op (Ana didn't add anything).

Pass --apply to write. Without --apply runs as a DRY RUN with full report.
"""
import argparse
import os
import xmlrpc.client
from collections import defaultdict
from pathlib import Path


def connect():
    env = Path(__file__).with_name(".promote.env")
    for raw in env.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    url = os.environ["DST_URL"].rstrip("/")
    db = os.environ["DST_DB"]
    key = os.environ["DST_API_KEY"]
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
    uid = common.authenticate(db, os.environ["DST_LOGIN"], key, {})
    m = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)
    def call(model, method, args, kwargs=None):
        return m.execute_kw(db, uid, key, model, method, args, kwargs or {})
    return call


def ptav_sig(call, ptav_ids):
    if not ptav_ids:
        return frozenset()
    rows = call("product.template.attribute.value", "read",
                [ptav_ids, ["attribute_id", "product_attribute_value_id"]])
    return frozenset(
        (r["attribute_id"][1] if r["attribute_id"] else None,
         r["product_attribute_value_id"][1] if r["product_attribute_value_id"] else None)
        for r in rows
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="actually write (default is dry-run)")
    ap.add_argument("--limit", type=int, default=0,
                    help="limit number of template pairs processed (0 = all)")
    ap.add_argument("--recover-only", action="store_true",
                    help="only fill missing refs (active=empty, archived has); "
                         "skip DIFF cases (where both have but differ).")
    args = ap.parse_args()

    call = connect()
    print(f"DST = {os.environ['DST_DB']}  {'APPLY' if args.apply else 'DRY RUN'}")

    # 1) Fetch all archived templates (sale_ok=True), key by name
    arch = call("product.template", "search_read",
                [[("active","=",False), ("sale_ok","=",True)]],
                {"fields": ["id","name","default_code","product_variant_ids"]})
    arch_by_name = defaultdict(list)
    for t in arch:
        arch_by_name[t["name"]].append(t)
    print(f"\nArchived templates (sale_ok): {len(arch)} across {len(arch_by_name)} unique names")

    # 2) Fetch all active templates, key by name
    active = call("product.template", "search_read",
                  [[("active","=",True), ("sale_ok","=",True)]],
                  {"fields": ["id","name","default_code","product_variant_ids"]})
    active_by_name = defaultdict(list)
    for t in active:
        active_by_name[t["name"]].append(t)
    print(f"Active templates (sale_ok):   {len(active)} across {len(active_by_name)} unique names")

    # 3) Pair them up
    pairs = []
    unmatched_arch = 0
    for name, group in arch_by_name.items():
        active_group = active_by_name.get(name)
        if not active_group:
            unmatched_arch += 1
            continue
        # pick most-recently-created archived (highest id)
        a = max(group, key=lambda x: x["id"])
        # pick most-recently-created active (highest id) -- typically only one
        v = max(active_group, key=lambda x: x["id"])
        pairs.append((a, v))
    print(f"Pairs found: {len(pairs)}  (archived names without active counterpart: {unmatched_arch})")

    if args.limit:
        pairs = pairs[:args.limit]
        print(f"(limited to first {args.limit} pairs)")

    # 4) Walk each pair: compute deltas
    tmpl_writes = []  # list of (active_id, vals)
    var_writes = []   # list of (active_var_id, vals)
    tmpl_recover = tmpl_diff = 0
    var_recover = var_diff = 0
    var_no_match = 0
    diff_samples = []  # to show user
    recover_samples = []

    for arch_t, act_t in pairs:
        # Template-level default_code
        arch_code = arch_t.get("default_code") or False
        act_code = act_t.get("default_code") or False
        if arch_code and arch_code != act_code:
            is_recover = not act_code
            if is_recover or not args.recover_only:
                tmpl_writes.append((act_t["id"], {"default_code": arch_code}))
            if act_code:
                tmpl_diff += 1
                if len(diff_samples) < 10:
                    diff_samples.append(("tmpl DIFF", arch_t["name"],
                                         act_code, arch_code))
            else:
                tmpl_recover += 1
                if len(recover_samples) < 10:
                    recover_samples.append(("tmpl RECOVER", arch_t["name"],
                                            "(empty)", arch_code))

        # Variant-level default_code.
        # IMPORTANT: archived template's `product_variant_ids` filters by
        # active=True by default (Odoo `active_test`), so we must search
        # product.product directly with `active_test: False` context.
        arch_v_data = call("product.product", "search_read",
                           [[("product_tmpl_id", "=", arch_t["id"])]],
                           {"fields": ["id","default_code","active",
                                       "product_template_attribute_value_ids"],
                            "context": {"active_test": False}})
        act_v_data = call("product.product", "search_read",
                          [[("product_tmpl_id", "=", act_t["id"])]],
                          {"fields": ["id","default_code","active",
                                      "product_template_attribute_value_ids"]})
        if not arch_v_data or not act_v_data:
            continue
        # Build ptav-keyed map of active
        act_by_sig = {}
        for v in act_v_data:
            sig = ptav_sig(call, v["product_template_attribute_value_ids"])
            act_by_sig[sig] = v
        # For each archived variant, find matching active
        for av in arch_v_data:
            ac = av.get("default_code") or False
            if not ac:
                continue  # archived has no code, nothing to recover
            sig = ptav_sig(call, av["product_template_attribute_value_ids"])
            actv = act_by_sig.get(sig)
            if not actv:
                var_no_match += 1
                continue
            cur = actv.get("default_code") or False
            if ac == cur:
                continue
            is_recover = not cur
            if is_recover or not args.recover_only:
                var_writes.append((actv["id"], {"default_code": ac}))
            if cur:
                var_diff += 1
            else:
                var_recover += 1

    print(f"\n=== TEMPLATE-LEVEL DELTAS ===")
    print(f"  recover (active empty, archived had):     {tmpl_recover}")
    print(f"  diff    (active has X, archived has Y):   {tmpl_diff}")
    print(f"  total template writes planned:            {len(tmpl_writes)}")
    print(f"\n=== VARIANT-LEVEL DELTAS ===")
    print(f"  recover (active empty, archived had):     {var_recover}")
    print(f"  diff    (active has X, archived has Y):   {var_diff}")
    print(f"  no archived->active ptav match (skip):    {var_no_match}")
    print(f"  total variant writes planned:             {len(var_writes)}")

    if recover_samples:
        print("\nSample RECOVER (templates):")
        for k, name, cur, new in recover_samples[:5]:
            print(f"  '{name}'  '{cur}' -> '{new}'")
    if diff_samples:
        print("\nSample DIFF (templates) [Ana's archived value wins]:")
        for k, name, cur, new in diff_samples[:5]:
            print(f"  '{name}'  '{cur}' -> '{new}'")

    if not args.apply:
        print("\n(dry run — pass --apply to execute)")
        return

    print("\n=== APPLYING ===")
    for act_id, vals in tmpl_writes:
        try:
            call("product.template", "write", [[act_id], vals])
        except Exception as exc:
            print(f"  ! tmpl#{act_id} write failed: {exc}")
    print(f"  applied {len(tmpl_writes)} template writes")
    for act_id, vals in var_writes:
        try:
            call("product.product", "write", [[act_id], vals])
        except Exception as exc:
            print(f"  ! var#{act_id} write failed: {exc}")
    print(f"  applied {len(var_writes)} variant writes")


if __name__ == "__main__":
    main()
