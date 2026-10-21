"""Dedup website categories (product.public.category) in DST.

Strategy:
- Group active categories in DST by name (case + accent insensitive).
- For each group with >1 record:
  - Pick canonical = the one with image_1920 set; if multiple, the oldest (smallest id)
  - If none has an image, canonical = oldest (smallest id)
  - For each non-canonical: walk all product.template.public_categ_ids that include it,
    replace with the canonical, then archive the non-canonical (active=False).

Pass --apply to actually write. Without --apply runs as a DRY RUN.
"""
import argparse
import os
import unicodedata
import xmlrpc.client
from collections import defaultdict
from pathlib import Path


def norm(s):
    if not s:
        return ""
    return "".join(c for c in unicodedata.normalize("NFD", s.lower().strip())
                   if unicodedata.category(c) != "Mn")


def connect(lbl):
    url = os.environ[f'{lbl}_URL'].rstrip('/'); db = os.environ[f'{lbl}_DB']
    key = os.environ[f'{lbl}_API_KEY']
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
    uid = common.authenticate(db, os.environ[f'{lbl}_LOGIN'], key, {})
    m = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)
    def call(model, method, args, kwargs=None):
        return m.execute_kw(db, uid, key, model, method, args, kwargs or {})
    return call


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="apply the dedup (default is dry-run)")
    args = ap.parse_args()

    env = Path(__file__).with_name(".promote.env")
    for raw in env.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip(chr(34)).strip(chr(39)))

    dst = connect('DST')
    print(f">>> DST = {os.environ['DST_DB']}  {'APPLY' if args.apply else 'DRY RUN'}\n")

    # 1) Fetch all categories with metadata (no active field on product.public.category in v19)
    cats = dst("product.public.category", "search_read",
               [[]],
               {"fields": ["id","name","parent_id","display_name","sequence","image_1920"]})
    print(f"Total categories in DST: {len(cats)}")

    # Group by normalized name + parent_id (since same name under different parents could be legitimate
    # — but the user said "duplicates with same display_name should be merged"; we go by name only first)
    by_norm = defaultdict(list)
    for c in cats:
        by_norm[norm(c["name"])].append(c)

    dupe_groups = {k: v for k, v in by_norm.items() if len(v) > 1}
    print(f"Duplicate name groups: {len(dupe_groups)}\n")

    total_to_repoint = 0
    total_to_archive = 0
    plan_lines = []
    actions = []  # list of dicts {'kind': 'repoint'|'archive', ...}

    skipped_ambiguous = []
    for norm_name, group in sorted(dupe_groups.items()):
        # SAFE rule: only auto-merge if exactly one record in the group has an image.
        # That one is the canonical (pre-existing in dst); the others (no image) are
        # what my promote created. Cases with multiple-image records or none-image
        # records are flagged for manual review.
        with_image = [c for c in group if c.get("image_1920")]
        without_image = [c for c in group if not c.get("image_1920")]
        if len(with_image) != 1 or len(without_image) == 0:
            skipped_ambiguous.append((norm_name, group))
            continue
        canonical = with_image[0]
        others = without_image

        # For each non-canonical, count how many product.template reference it
        non_canon_with_products = []
        for c in others:
            tmpl_ids = dst("product.template", "search",
                           [[("public_categ_ids", "in", [c["id"]])]], {})
            non_canon_with_products.append((c, tmpl_ids))

        # How many products on the canonical itself?
        canonical_tmpls = dst("product.template", "search",
                              [[("public_categ_ids", "in", [canonical["id"]])]], {})
        plan_lines.append(f"\n--- group '{group[0]['name']}' (norm='{norm_name}') ---")
        plan_lines.append(f"  CANONICAL : id={canonical['id']}  "
                          f"has_image={bool(canonical.get('image_1920'))}  "
                          f"templates_referencing={len(canonical_tmpls)}  "
                          f"display='{canonical.get('display_name')}'")
        for c, tmpl_ids in non_canon_with_products:
            plan_lines.append(f"  to-delete : id={c['id']}  has_image={bool(c.get('image_1920'))}  "
                              f"templates_referencing={len(tmpl_ids)}  "
                              f"display='{c.get('display_name')}'")
            if tmpl_ids:
                actions.append({"kind": "repoint", "from": c["id"], "to": canonical["id"],
                                "tmpl_ids": tmpl_ids})
                total_to_repoint += len(tmpl_ids)
            actions.append({"kind": "delete", "id": c["id"]})
            total_to_archive += 1

    print("\n".join(plan_lines))
    if skipped_ambiguous:
        print(f"\n=== SKIPPED (ambiguous - manual review required) ===")
        for norm_name, group in skipped_ambiguous:
            print(f"  '{group[0]['name']}' (norm='{norm_name}'):")
            for c in group:
                tmpl_count = dst("product.template", "search_count",
                                 [[("public_categ_ids", "in", [c["id"]])]])
                print(f"    id={c['id']:>5}  has_image={bool(c.get('image_1920'))}  "
                      f"templates={tmpl_count}  display='{c.get('display_name')}'")
    print(f"\n=== PLAN SUMMARY ===")
    print(f"  product.template re-points: {total_to_repoint}")
    print(f"  categories to delete:       {total_to_archive}")
    print(f"  groups skipped (ambiguous): {len(skipped_ambiguous)}")

    if not args.apply:
        print("\n(dry run — pass --apply to execute)")
        return

    print("\n=== APPLYING ===")
    # Execute repoints
    for a in actions:
        if a["kind"] == "repoint":
            # Read current categs, swap from->to
            tmpls = dst("product.template", "read", [a["tmpl_ids"]],
                        {"fields": ["id", "public_categ_ids"]})
            for t in tmpls:
                new_ids = [c for c in t["public_categ_ids"] if c != a["from"]]
                if a["to"] not in new_ids:
                    new_ids.append(a["to"])
                dst("product.template", "write",
                    [[t["id"]], {"public_categ_ids": [(6, 0, new_ids)]}])
            print(f"  repointed {len(a['tmpl_ids'])} template(s) from categ#{a['from']} -> #{a['to']}")
        elif a["kind"] == "delete":
            try:
                dst("product.public.category", "unlink", [[a["id"]]])
                print(f"  deleted categ#{a['id']}")
            except Exception as exc:
                print(f"  ! could not delete categ#{a['id']}: {exc}")


if __name__ == "__main__":
    main()
