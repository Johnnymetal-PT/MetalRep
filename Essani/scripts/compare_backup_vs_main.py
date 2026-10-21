"""Data study: SRC (backup 10/05 18:07) vs DST (current main).

Read-only comparison covering:
- Counts summary (templates, variants, codes, images, docs)
- Templates only in SRC (missing in DST) / only in DST (extra)
- Field deltas in matched pairs (default_code, is_published, public_categ names,
  variants count, hide_on_website)
- Variant-level default_code coverage
- Public categories: count + duplicate-name groups in DST
- Sample listings for each delta category

Output goes to stdout + scripts/_compare_report.txt.
"""
import os
import xmlrpc.client
from collections import Counter, defaultdict
from pathlib import Path

env = Path('scripts/.promote.env')
for raw in env.read_text(encoding='utf-8').splitlines():
    line = raw.strip()
    if not line or line.startswith('#') or '=' not in line: continue
    k, v = line.split('=', 1)
    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def connect(lbl):
    url = os.environ[f'{lbl}_URL'].rstrip('/'); db = os.environ[f'{lbl}_DB']
    key = os.environ[f'{lbl}_API_KEY']
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
    uid = common.authenticate(db, os.environ[f'{lbl}_LOGIN'], key, {})
    m = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)
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


report_lines = []
def out(msg=""):
    print(msg)
    report_lines.append(msg)


def section(title):
    out("\n" + "=" * 78)
    out(f"  {title}")
    out("=" * 78)


def main():
    src = connect('SRC'); dst = connect('DST')
    out(f"SRC = {os.environ['SRC_DB']}  (backup 2026-05-10 18:07)")
    out(f"DST = {os.environ['DST_DB']}  (current main)")

    # ========== 1) COUNTS SUMMARY ==========
    section("1) COUNTS SUMMARY")
    metrics = [
        ("templates active sale_ok",
         lambda c: c("product.template", "search_count",
                     [[("active","=",True),("sale_ok","=",True)]])),
        ("templates active sale_ok with default_code",
         lambda c: c("product.template", "search_count",
                     [[("active","=",True),("sale_ok","=",True),("default_code","!=",False)]])),
        ("templates active sale_ok published",
         lambda c: c("product.template", "search_count",
                     [[("active","=",True),("sale_ok","=",True),("is_published","=",True)]])),
        ("variants active",
         lambda c: c("product.product", "search_count", [[("active","=",True)]])),
        ("variants active with default_code",
         lambda c: c("product.product", "search_count",
                     [[("active","=",True),("default_code","!=",False)]])),
        ("variants active hide_on_website=True",
         lambda c: c("product.product", "search_count",
                     [[("active","=",True),("hide_on_website","=",True)]])),
        ("product.image (template level)",
         lambda c: c("product.image", "search_count",
                     [[("product_variant_id","=",False)]])),
        ("product.image (variant level)",
         lambda c: c("product.image", "search_count",
                     [[("product_variant_id","!=",False)]])),
        ("product.document on product.template",
         lambda c: c("product.document", "search_count",
                     [[("res_model","=","product.template")]])),
        ("product.document on product.product",
         lambda c: c("product.document", "search_count",
                     [[("res_model","=","product.product")]])),
        ("product.public.category total",
         lambda c: c("product.public.category", "search_count", [[]])),
    ]
    out(f"\n{'metric':<55} {'SRC':>10} {'DST':>10} {'diff':>10}")
    out("-" * 88)
    for name, fn in metrics:
        try:
            s = fn(src)
        except Exception as exc:
            s = f"ERR:{exc}"
        try:
            d = fn(dst)
        except Exception as exc:
            d = f"ERR:{exc}"
        delta = d - s if isinstance(s, int) and isinstance(d, int) else "-"
        out(f"{name:<55} {s!s:>10} {d!s:>10} {delta!s:>10}")

    # ========== 2) TEMPLATE PAIRING BY NAME ==========
    section("2) TEMPLATE PAIRING BY NAME (sale_ok=True)")
    src_t = src("product.template", "search_read",
                [[("active","=",True),("sale_ok","=",True)]],
                {"fields": ["id","name","default_code","is_published",
                            "public_categ_ids","product_variant_ids",
                            "product_template_image_ids","product_document_ids"]})
    dst_t = dst("product.template", "search_read",
                [[("active","=",True),("sale_ok","=",True)]],
                {"fields": ["id","name","default_code","is_published",
                            "public_categ_ids","product_variant_ids",
                            "product_template_image_ids","product_document_ids"]})
    src_by_name = defaultdict(list)
    dst_by_name = defaultdict(list)
    for t in src_t: src_by_name[t["name"]].append(t)
    for t in dst_t: dst_by_name[t["name"]].append(t)
    src_names = set(src_by_name.keys())
    dst_names = set(dst_by_name.keys())
    only_src = src_names - dst_names
    only_dst = dst_names - src_names
    common = src_names & dst_names
    out(f"  SRC unique names: {len(src_names)}  total records: {len(src_t)}")
    out(f"  DST unique names: {len(dst_names)}  total records: {len(dst_t)}")
    out(f"  names only in SRC (MISSING in DST): {len(only_src)}")
    out(f"  names only in DST (EXTRA, not in backup): {len(only_dst)}")
    out(f"  names in both (matched pairs):      {len(common)}")

    if only_src:
        out("\n  >> Sample of templates in SRC but missing in DST:")
        for name in sorted(only_src)[:15]:
            t = src_by_name[name][0]
            out(f"     src#{t['id']:>5} pub={t.get('is_published')!s:5} '{name}'")
        if len(only_src) > 15:
            out(f"     ... and {len(only_src)-15} more")
    if only_dst:
        out("\n  >> Sample of templates in DST but not in backup SRC:")
        for name in sorted(only_dst)[:15]:
            t = dst_by_name[name][0]
            out(f"     dst#{t['id']:>5} pub={t.get('is_published')!s:5} '{name}'")
        if len(only_dst) > 15:
            out(f"     ... and {len(only_dst)-15} more")

    # ========== 3) FIELD-LEVEL DELTAS in matched pairs ==========
    section("3) FIELD DELTAS IN MATCHED PAIRS")
    delta_code = 0  # different default_code (template)
    delta_pub = 0   # different is_published
    delta_var_count = 0
    delta_img_count = 0
    delta_doc_count = 0
    samples = defaultdict(list)
    pairs = []  # (src_t, dst_t) for use in next section
    for name in common:
        s = max(src_by_name[name], key=lambda x: x["id"])
        d = max(dst_by_name[name], key=lambda x: x["id"])
        pairs.append((s, d))
        sc = s.get("default_code") or ""
        dc = d.get("default_code") or ""
        if sc != dc:
            delta_code += 1
            if len(samples["code"]) < 8:
                samples["code"].append((name, sc, dc))
        if bool(s.get("is_published")) != bool(d.get("is_published")):
            delta_pub += 1
            if len(samples["pub"]) < 8:
                samples["pub"].append((name, s.get("is_published"), d.get("is_published")))
        s_v = len(s.get("product_variant_ids") or [])
        d_v = len(d.get("product_variant_ids") or [])
        if s_v != d_v:
            delta_var_count += 1
            if len(samples["varcount"]) < 8:
                samples["varcount"].append((name, s_v, d_v))
        s_i = len(s.get("product_template_image_ids") or [])
        d_i = len(d.get("product_template_image_ids") or [])
        if s_i != d_i:
            delta_img_count += 1
            if len(samples["imgcount"]) < 8:
                samples["imgcount"].append((name, s_i, d_i))
        s_d = len(s.get("product_document_ids") or [])
        d_d = len(d.get("product_document_ids") or [])
        if s_d != d_d:
            delta_doc_count += 1
            if len(samples["doccount"]) < 8:
                samples["doccount"].append((name, s_d, d_d))

    out(f"  pairs with different default_code:        {delta_code}")
    out(f"  pairs with different is_published:        {delta_pub}")
    out(f"  pairs with different variant count:       {delta_var_count}")
    out(f"  pairs with different template-img count:  {delta_img_count}")
    out(f"  pairs with different document count:      {delta_doc_count}")

    def show(key, label):
        if not samples[key]: return
        out(f"\n  >> Sample {label}:")
        for row in samples[key][:8]:
            out(f"     {row}")
    show("code", "default_code (template) SRC vs DST")
    show("pub", "is_published SRC vs DST")
    show("varcount", "variant count SRC vs DST")
    show("imgcount", "template-img count SRC vs DST")
    show("doccount", "document count SRC vs DST")

    # ========== 4) VARIANT-LEVEL DELTAS (sample of pairs) ==========
    section("4) VARIANT-LEVEL DELTAS (in matched template pairs)")
    var_total_pairs = 0
    var_code_diff = 0
    var_hide_diff = 0
    var_no_match = 0
    var_only_src = 0
    var_only_dst = 0
    sample_var_code = []
    sample_var_hide = []
    pair_limit = len(pairs)
    out(f"  processing {pair_limit} template pairs...")
    for s, d in pairs:
        s_vars = src("product.product", "search_read",
                     [[("product_tmpl_id","=",s["id"])]],
                     {"fields": ["id","default_code","hide_on_website",
                                 "product_template_attribute_value_ids"]})
        d_vars = dst("product.product", "search_read",
                     [[("product_tmpl_id","=",d["id"])]],
                     {"fields": ["id","default_code","hide_on_website",
                                 "product_template_attribute_value_ids"]})
        s_by_sig = {}
        for v in s_vars:
            sig = ptav_sig(src, v["product_template_attribute_value_ids"])
            s_by_sig[sig] = v
        d_by_sig = {}
        for v in d_vars:
            sig = ptav_sig(dst, v["product_template_attribute_value_ids"])
            d_by_sig[sig] = v
        common_sigs = set(s_by_sig) & set(d_by_sig)
        var_total_pairs += len(common_sigs)
        var_only_src += len(set(s_by_sig) - common_sigs)
        var_only_dst += len(set(d_by_sig) - common_sigs)
        for sig in common_sigs:
            sv = s_by_sig[sig]
            dv = d_by_sig[sig]
            sc = sv.get("default_code") or ""
            dc = dv.get("default_code") or ""
            if sc != dc:
                var_code_diff += 1
                if len(sample_var_code) < 8:
                    sample_var_code.append((s["name"], sc, dc))
            if bool(sv.get("hide_on_website")) != bool(dv.get("hide_on_website")):
                var_hide_diff += 1
                if len(sample_var_hide) < 8:
                    sample_var_hide.append((s["name"], sv.get("hide_on_website"), dv.get("hide_on_website")))
    out(f"  variant pairs matched (same ptav sig): {var_total_pairs}")
    out(f"  variants only in SRC (no DST counterpart): {var_only_src}")
    out(f"  variants only in DST (no SRC counterpart): {var_only_dst}")
    out(f"  variant pairs with different default_code: {var_code_diff}")
    out(f"  variant pairs with different hide_on_website: {var_hide_diff}")
    if sample_var_code:
        out("\n  >> Sample variant default_code deltas (SRC vs DST):")
        for r in sample_var_code:
            out(f"     {r}")
    if sample_var_hide:
        out("\n  >> Sample variant hide_on_website deltas (SRC vs DST):")
        for r in sample_var_hide:
            out(f"     {r}")

    # ========== 5) PUBLIC CATEGORIES ==========
    section("5) PUBLIC CATEGORIES")
    src_c = src("product.public.category", "search_read", [[]],
                {"fields": ["id","name","parent_id","image_1920"]})
    dst_c = dst("product.public.category", "search_read", [[]],
                {"fields": ["id","name","parent_id","image_1920"]})
    out(f"  SRC categories: {len(src_c)}")
    out(f"  DST categories: {len(dst_c)}")
    # Duplicate names in DST
    dst_by_norm = defaultdict(list)
    for c in dst_c:
        dst_by_norm[c["name"]].append(c)
    dst_dupes = {k: v for k, v in dst_by_norm.items() if len(v) > 1}
    out(f"  DST duplicate name groups (case-sensitive): {len(dst_dupes)}")
    if dst_dupes:
        out("  >> sample of duplicates in DST:")
        for name, group in list(dst_dupes.items())[:10]:
            out(f"     '{name}' ({len(group)}x): ids={[c['id'] for c in group]}")
    src_by_norm = defaultdict(list)
    for c in src_c: src_by_norm[c["name"]].append(c)
    src_dupes = {k: v for k, v in src_by_norm.items() if len(v) > 1}
    out(f"  SRC duplicate name groups: {len(src_dupes)}")

    # ========== 6) WRITE REPORT ==========
    out_path = Path("scripts/_compare_report.txt")
    out_path.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"\n(report saved to {out_path})")


if __name__ == "__main__":
    main()
