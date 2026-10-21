"""Characterize variants that exist on only one side (backup vs main).

Read-only. Pairs templates by name, matches variants by ptav signature,
then profiles the only-in-DST and only-in-SRC variants: do they carry a
reference / price, are they hidden, and on which templates do they cluster?
"""
import os, time, xmlrpc.client
from collections import defaultdict, Counter
from pathlib import Path

env = Path('scripts/.promote.env')
for raw in env.read_text(encoding='utf-8').splitlines():
    line = raw.strip()
    if not line or line.startswith('#') or '=' not in line:
        continue
    k, v = line.split('=', 1)
    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def connect(prefix):
    url = os.environ[f'{prefix}_URL'].rstrip('/')
    db = os.environ[f'{prefix}_DB']
    login = os.environ[f'{prefix}_LOGIN']
    key = os.environ[f'{prefix}_API_KEY']
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
    uid = common.authenticate(db, login, key, {})
    m = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)

    def call(model, method, args, kw=None):
        last = None
        for attempt in range(6):
            try:
                return m.execute_kw(db, uid, key, model, method, args, kw or {})
            except (xmlrpc.client.ProtocolError, OSError) as exc:
                last = exc
                time.sleep(2 * (attempt + 1))  # 2,4,6,8,10s backoff
        raise last
    return call


# ptav signature cache per connection
_ptav_cache = {}
def ptav_sig(tag, call, ptav_ids):
    if not ptav_ids:
        return frozenset()
    key = (tag, tuple(sorted(ptav_ids)))
    if key in _ptav_cache:
        return _ptav_cache[key]
    rows = call("product.template.attribute.value", "read",
                [ptav_ids, ["attribute_id", "product_attribute_value_id"]])
    sig = frozenset(
        (r["attribute_id"][1] if r["attribute_id"] else None,
         r["product_attribute_value_id"][1] if r["product_attribute_value_id"] else None)
        for r in rows)
    _ptav_cache[key] = sig
    return sig


VFIELDS = ["id", "default_code", "lst_price", "hide_on_website",
           "product_template_attribute_value_ids"]


def load_templates(call):
    rows = call("product.template", "search_read",
                [[("active", "=", True), ("sale_ok", "=", True)]],
                {"fields": ["id", "name"]})
    by_name = defaultdict(list)
    for t in rows:
        by_name[t["name"]].append(t)
    return by_name


def profile(label, items):
    """items: list of dicts {tmpl, code, price, hidden}"""
    n = len(items)
    with_code = sum(1 for it in items if it["code"])
    hidden = sum(1 for it in items if it["hidden"])
    priced = sum(1 for it in items if it["price"])
    print(f"\n  {label}: {n} variants")
    print(f"    with default_code (real ref): {with_code}  ({100*with_code//n if n else 0}%)")
    print(f"    hide_on_website=True:          {hidden}  ({100*hidden//n if n else 0}%)")
    print(f"    lst_price > 0:                 {priced}  ({100*priced//n if n else 0}%)")
    by_tmpl = Counter(it["tmpl"] for it in items)
    print(f"    spread over {len(by_tmpl)} templates; top 15 by count:")
    for name, c in by_tmpl.most_common(15):
        print(f"      {c:>3}x  {name}")
    coded = [it for it in items if it["code"]]
    if coded:
        print(f"    --- the {len(coded)} WITH a reference (template | ref | price | hidden) ---")
        for it in sorted(coded, key=lambda x: (x["tmpl"], x["code"])):
            print(f"      {it['tmpl'][:45]:<45} | {it['code']:<22} | {it['price']:>8} | hidden={it['hidden']}")


def main():
    src = connect('SRC'); dst = connect('DST')
    src_by_name = load_templates(src)
    dst_by_name = load_templates(dst)
    common = set(src_by_name) & set(dst_by_name)
    print(f"matched template names: {len(common)}")

    only_dst_items = []   # variants on main with no backup counterpart
    only_src_items = []   # variants on backup with no main counterpart

    for i, name in enumerate(sorted(common), 1):
        if i % 50 == 0:
            print(f"  ...{i}/{len(common)} templates processed")
        s_t = max(src_by_name[name], key=lambda x: x["id"])
        d_t = max(dst_by_name[name], key=lambda x: x["id"])
        s_vars = src("product.product", "search_read",
                     [[("product_tmpl_id", "=", s_t["id"])]], {"fields": VFIELDS})
        d_vars = dst("product.product", "search_read",
                     [[("product_tmpl_id", "=", d_t["id"])]], {"fields": VFIELDS})
        s_by_sig = {ptav_sig('S', src, v["product_template_attribute_value_ids"]): v for v in s_vars}
        d_by_sig = {ptav_sig('D', dst, v["product_template_attribute_value_ids"]): v for v in d_vars}
        common_sigs = set(s_by_sig) & set(d_by_sig)
        for sig in set(d_by_sig) - common_sigs:
            v = d_by_sig[sig]
            only_dst_items.append({"tmpl": name, "code": v.get("default_code") or "",
                                   "price": v.get("lst_price") or 0, "hidden": bool(v.get("hide_on_website"))})
        for sig in set(s_by_sig) - common_sigs:
            v = s_by_sig[sig]
            only_src_items.append({"tmpl": name, "code": v.get("default_code") or "",
                                   "price": v.get("lst_price") or 0, "hidden": bool(v.get("hide_on_website"))})

    print("\n" + "=" * 70)
    print("  VARIANT DELTA CHARACTERIZATION")
    print("=" * 70)
    profile("ONLY IN MAIN (extra on Plataforma, not in backup)", only_dst_items)
    profile("ONLY IN BACKUP (missing from Plataforma)", only_src_items)


if __name__ == "__main__":
    main()
