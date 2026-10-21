#!/usr/bin/env python3
"""
Promote a curated set of products from Staging to Production (Odoo 19, Odoo.sh).

One-shot replication of `product.template` records (with variants, template
and variant images, extra `product.image`, and `product.document`) from a
source database to a target database via XML-RPC.

Idempotent: upserts `product.template` by `default_code` when present, falling
back to an `ir.model.data` external ID `__promote__.tmpl_<src_id>` created on
first promotion. On update, `attribute_line_ids` is NOT touched (rewriting it
would re-generate variants and break stock/sales references).

USAGE
-----
1. In both databases: Settings > Users > <your user> > Account Security >
   New API Key. Copy each value.
2. Copy scripts/promote_products.env.example to scripts/.promote.env and fill
   the SRC_* / DST_* values.
3. Identify the products in Staging (pick ONE selector):
     --ids 12,15,23                  # product.template ids in the source DB
     --codes ABC-1,ABC-2             # default_code values
     --domain '[["categ_id.complete_name","=","All / Cat"]]'
4. Dry-run first:
     python scripts/promote_products.py --env scripts/.promote.env \
            --ids 12,15 --dry-run --verbose
5. Promote:
     python scripts/promote_products.py --env scripts/.promote.env --ids 12,15

NOTES
-----
- Pre-requisites (`product.category`, `uom.uom`, `product.attribute`,
  `product.attribute.value`, `product.tag`) are created in the target if absent,
  matched by name (category chain matched by `name` + `parent_id`).
- Variants are auto-generated in the target by writing `attribute_line_ids` on
  the template; the script then matches source<->target variants by the set of
  (attribute_name, value_name) on `product_template_attribute_value_ids` and
  writes variant-specific fields and images.
- Documents (`product.document`) are copied with their binary `datas`; dedup
  by (name, res_model, res_id).
- The source DB is never written to.

LIMITATIONS
-----------
- Attributes with `create_variant='dynamic'` are supported for template setup,
  but variants must already exist on the source (the matcher only writes to
  existing target variants triggered by the attribute lines).
- Suppliers (`seller_ids`), BoMs, routes, taxes and accounting fields are NOT
  copied. Add them to TEMPLATE_FIELDS / a dedicated helper if needed.
"""

import argparse
import http.client
import json
import logging
import os
import sys
import time
import xmlrpc.client
from pathlib import Path

# Transient network errors are retried only for read/idempotent-write methods;
# create/unlink-by-id are skipped to avoid duplicates if the server already
# committed before the connection dropped.
_SAFE_RETRY_METHODS = {"search", "search_read", "read", "write", "fields_get"}
_RETRY_DELAYS = [2, 5, 10, 20, 40]
# Odoo.sh proxies briefly return 404 to all requests during a rolling deploy;
# treat 404 the same as 5xx for safe-method retries.
_RETRY_HTTP_CODES = {404, 500, 502, 503, 504}

# Odoo.sh enforces a request body cap (~100 MB). Files larger than this cannot
# be uploaded via XML-RPC and must be attached manually via the Odoo UI.
_MAX_DOC_BYTES = 95 * 1024 * 1024

# Per-template manual overrides. Keys are Staging product.template ids.
# - skip_attribute_names: drop attribute_lines whose source attribute name matches.
# - dynamic_clone_attribute_names: for these source attribute names, use a
#   dedicated `<name> (dinamica)` clone in the destination with
#   create_variant='dynamic', so variants are generated on demand instead of
#   exploding the cartesian (and other templates that use the original
#   attribute are not affected).
_TEMPLATE_OVERRIDES = {
    2139: {"skip_attribute_names": {"Potencia"}},          # drop the duplicate (without accent); variants use the with-accent one
    2015: {"dynamic_clone_attribute_names": {"Configuração"}},
}


# ---------------------------------------------------------------------------
# Fields explicitly copied. Unknown fields are silently dropped by filter_vals
# so the script stays portable across minor version differences.
# ---------------------------------------------------------------------------
TEMPLATE_SCALAR_FIELDS = [
    'name', 'default_code', 'barcode', 'active',
    'sale_ok', 'purchase_ok', 'is_published',
    'list_price', 'standard_price',
    'description', 'description_sale', 'description_purchase',
    'description_ecommerce', 'public_description',
    'description_pickingin', 'description_pickingout',
    'weight', 'volume',
    'image_1920',
    'type', 'is_storable', 'detailed_type',
    'tracking', 'invoice_policy',
    'service_type', 'service_tracking',
    'website_sequence', 'website_size_x', 'website_size_y',
    'allow_out_of_stock_order', 'show_availability', 'available_threshold',
    'base_unit_count', 'compare_list_price',
    'product_tooltip',
    'country_of_origin',
]
TEMPLATE_REL_FIELDS = [
    'categ_id', 'uom_id', 'uom_po_id', 'product_tag_ids',
    'attribute_line_ids', 'product_variant_ids',
    'product_template_image_ids', 'product_document_ids',
    'public_categ_ids', 'website_ribbon_id', 'base_unit_id',
    # 2nd-pass relations (cross-sells; written only after every template exists in dst)
    'alternative_product_ids', 'accessory_product_ids', 'optional_product_ids',
]
# Cross-sell relations handled in the 2nd pass — kept out of the 1st-pass create/update.
CROSS_SELL_TEMPLATE_FIELDS = [
    'alternative_product_ids',   # m2m to product.template
    'optional_product_ids',      # m2m to product.template
    'accessory_product_ids',     # m2m to product.product
]
VARIANT_FIELDS = [
    'default_code', 'barcode', 'active',
    'lst_price', 'standard_price',
    'weight', 'volume',
    'image_variant_1920',
    'description_pickingin', 'description_pickingout',
    'product_tooltip',
    # Custom fields from local modules
    'hide_on_website',  # pg_website_hide_unavailable_variant
]
IMAGE_FIELDS = ['name', 'image_1920', 'sequence']
DOCUMENT_FIELDS = [
    'name', 'datas', 'mimetype', 'type', 'url',
    'res_model', 'res_id',
    'shown_on_product_page', 'attached_on_mobile', 'attached_on',
]


# ---------------------------------------------------------------------------
# Plumbing
# ---------------------------------------------------------------------------
def setup_logging(verbose: bool) -> logging.Logger:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    return logging.getLogger("promote")


def load_env(env_path):
    if not env_path:
        return
    p = Path(env_path)
    if not p.exists():
        raise FileNotFoundError(f"env file not found: {env_path}")
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


class OdooClient:
    """Minimal XML-RPC wrapper, with a fields_get cache for safe value filtering."""

    def __init__(self, url, db, login, api_key, label, log):
        self.url = url.rstrip("/")
        self.db = db
        self.login = login
        self.api_key = api_key
        self.label = label
        self.log = log
        common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common", allow_none=True)
        self.uid = common.authenticate(db, login, api_key, {})
        if not self.uid:
            raise RuntimeError(f"[{label}] authentication failed db={db} user={login}")
        self.models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object", allow_none=True)
        self._fields_cache = {}
        log.info(f"[{label}] connected {self.url} db={db} uid={self.uid}")

    def kw(self, model, method, args, kwargs=None):
        retries = len(_RETRY_DELAYS) if method in _SAFE_RETRY_METHODS else 0
        for attempt in range(retries + 1):
            try:
                return self.models.execute_kw(
                    self.db, self.uid, self.api_key, model, method, args, kwargs or {}
                )
            except (ConnectionResetError, ConnectionAbortedError, TimeoutError, OSError,
                    http.client.HTTPException) as exc:
                if attempt >= retries:
                    raise
                delay = _RETRY_DELAYS[attempt]
                self.log.warning(
                    f"  ! {self.label} {model}.{method} {type(exc).__name__}: {exc} "
                    f"-- retry {attempt+1}/{retries} in {delay}s"
                )
                time.sleep(delay)
                # On HTTPException, the xmlrpc Transport may keep a broken
                # connection cached -- force a fresh ServerProxy for retries.
                self.models = xmlrpc.client.ServerProxy(
                    f"{self.url}/xmlrpc/2/object", allow_none=True
                )
            except xmlrpc.client.ProtocolError as exc:
                if exc.errcode not in _RETRY_HTTP_CODES or attempt >= retries:
                    raise
                delay = _RETRY_DELAYS[attempt]
                self.log.warning(
                    f"  ! {self.label} {model}.{method} HTTP {exc.errcode} "
                    f"-- retry {attempt+1}/{retries} in {delay}s"
                )
                time.sleep(delay)

    def search(self, model, domain, **kw):
        return self.kw(model, "search", [domain], kw)

    def read(self, model, ids, fields):
        if not ids:
            return []
        return self.kw(model, "read", [ids, fields])

    def search_read(self, model, domain, fields, **kw):
        kw["fields"] = fields
        return self.kw(model, "search_read", [domain], kw)

    def create(self, model, vals):
        return self.kw(model, "create", [vals])

    def write(self, model, ids, vals):
        return self.kw(model, "write", [ids, vals])

    def unlink(self, model, ids):
        return self.kw(model, "unlink", [ids])

    def model_fields(self, model):
        if model not in self._fields_cache:
            self._fields_cache[model] = self.kw(
                model, "fields_get", [], {"attributes": ["type", "readonly", "store"]},
            )
        return self._fields_cache[model]

    def filter_vals(self, model, vals):
        """Drop fields that don't exist or are readonly on the target model.
        Keeps non-stored fields (e.g. company_dependent) since those are writable."""
        meta = self.model_fields(model)
        out = {}
        for k, v in vals.items():
            info = meta.get(k)
            if not info:
                continue
            if info.get("readonly"):
                continue
            out[k] = v
        return out


# ---------------------------------------------------------------------------
# Master-data mapping (src_id -> dst_id), idempotent by business key
# ---------------------------------------------------------------------------
class Mapper:
    def __init__(self, src: OdooClient, dst: OdooClient, log: logging.Logger, dry_run: bool):
        self.src = src
        self.dst = dst
        self.log = log
        self.dry_run = dry_run
        self.category_cache = {}
        self.uom_category_cache = {}
        self.uom_cache = {}
        self.attribute_cache = {}
        self.attribute_value_cache = {}
        self.tag_cache = {}
        self.variant_map = {}  # src product.product id -> dst product.product id
        self.template_map = {}  # src product.template id -> dst product.template id
        self.public_categ_cache = {}
        self.ribbon_cache = {}

    def _create(self, model, vals, label):
        if self.dry_run:
            self.log.info(f"  [DRY] would create {model} ({label}) vals={list(vals.keys())}")
            return -1
        new_id = self.dst.create(model, vals)
        self.log.info(f"  + {model} created id={new_id} ({label})")
        return new_id

    def map_category(self, src_id):
        if not src_id:
            return False
        if src_id in self.category_cache:
            return self.category_cache[src_id]
        cat = self.src.read("product.category", [src_id], ["name", "parent_id"])[0]
        parent_dst = self.map_category(cat["parent_id"][0]) if cat["parent_id"] else False
        domain = [("name", "=", cat["name"]),
                  ("parent_id", "=", parent_dst if parent_dst else False)]
        ids = self.dst.search("product.category", domain, limit=1)
        if ids:
            dst_id = ids[0]
        else:
            vals = {"name": cat["name"]}
            if parent_dst:
                vals["parent_id"] = parent_dst
            dst_id = self._create("product.category", vals, cat["name"])
        self.category_cache[src_id] = dst_id
        return dst_id

    def map_uom(self, src_id):
        """Map a uom.uom across DBs by name; create in target if missing.

        v18+ removed `uom.category`; UoMs now form a self-referencing tree via
        `relative_uom_id`. Older code paths (`category_id`, `uom_type`) are
        kept conditionally for forward/backward compatibility.
        """
        if not src_id:
            return False
        if src_id in self.uom_cache:
            return self.uom_cache[src_id]
        src_fields = self.src.model_fields("uom.uom")
        candidates = ["name", "factor", "rounding", "relative_factor",
                      "relative_uom_id", "sequence", "active",
                      "category_id", "uom_type"]
        read_fields = [f for f in candidates if f in src_fields]
        uom = self.src.read("uom.uom", [src_id], read_fields)[0]
        ids = self.dst.search("uom.uom", [("name", "=", uom["name"])], limit=1)
        if ids:
            dst_id = ids[0]
        else:
            vals = {"name": uom["name"]}
            for f in ("factor", "rounding", "relative_factor", "sequence", "active", "uom_type"):
                if f in uom and uom[f] is not None:
                    vals[f] = uom[f]
            if uom.get("relative_uom_id"):
                rel_src = uom["relative_uom_id"][0]
                # guard against the reference UoM pointing to itself
                if rel_src != src_id:
                    vals["relative_uom_id"] = self.map_uom(rel_src)
            dst_id = self._create(
                "uom.uom", self.dst.filter_vals("uom.uom", vals), uom["name"]
            )
        self.uom_cache[src_id] = dst_id
        return dst_id

    def map_attribute(self, src_id):
        if not src_id:
            return False
        if src_id in self.attribute_cache:
            return self.attribute_cache[src_id]
        attr = self.src.read(
            "product.attribute", [src_id],
            ["name", "create_variant", "display_type", "sequence"],
        )[0]
        ids = self.dst.search("product.attribute", [("name", "=", attr["name"])], limit=1)
        if ids:
            dst_id = ids[0]
        else:
            vals = {
                "name": attr["name"],
                "create_variant": attr.get("create_variant") or "always",
                "display_type": attr.get("display_type") or "radio",
                "sequence": attr.get("sequence") or 10,
            }
            dst_id = self._create(
                "product.attribute",
                self.dst.filter_vals("product.attribute", vals),
                attr["name"],
            )
        self.attribute_cache[src_id] = dst_id
        return dst_id

    def map_attribute_value(self, src_id):
        if not src_id:
            return False
        if src_id in self.attribute_value_cache:
            return self.attribute_value_cache[src_id]
        v = self.src.read(
            "product.attribute.value", [src_id],
            ["name", "attribute_id", "sequence", "html_color", "image", "default_extra_price"],
        )[0]
        dst_attr = self.map_attribute(v["attribute_id"][0])
        ids = self.dst.search(
            "product.attribute.value",
            [("name", "=", v["name"]), ("attribute_id", "=", dst_attr)],
            limit=1,
        )
        if ids:
            dst_id = ids[0]
        else:
            vals = {
                "name": v["name"],
                "attribute_id": dst_attr,
                "sequence": v.get("sequence") or 10,
            }
            for opt in ("html_color", "image", "default_extra_price"):
                if v.get(opt):
                    vals[opt] = v[opt]
            dst_id = self._create(
                "product.attribute.value",
                self.dst.filter_vals("product.attribute.value", vals),
                v["name"],
            )
        self.attribute_value_cache[src_id] = dst_id
        return dst_id

    def map_tag(self, src_id):
        if not src_id:
            return False
        if src_id in self.tag_cache:
            return self.tag_cache[src_id]
        tag = self.src.read("product.tag", [src_id], ["name"])[0]
        ids = self.dst.search("product.tag", [("name", "=", tag["name"])], limit=1)
        dst_id = ids[0] if ids else self._create("product.tag", {"name": tag["name"]}, tag["name"])
        self.tag_cache[src_id] = dst_id
        return dst_id

    def map_public_category(self, src_id):
        """Map product.public.category by hierarchy (name + parent_id), creating if missing."""
        if not src_id:
            return False
        if src_id in self.public_categ_cache:
            return self.public_categ_cache[src_id]
        src_fields = self.src.model_fields("product.public.category")
        read_fields = [f for f in ("name", "parent_id", "sequence", "website_id") if f in src_fields]
        cat = self.src.read("product.public.category", [src_id], read_fields)[0]
        parent_dst = self.map_public_category(cat["parent_id"][0]) if cat.get("parent_id") else False
        domain = [("name", "=", cat["name"]),
                  ("parent_id", "=", parent_dst if parent_dst else False)]
        ids = self.dst.search("product.public.category", domain, limit=1)
        if ids:
            dst_id = ids[0]
        else:
            vals = {"name": cat["name"]}
            if parent_dst:
                vals["parent_id"] = parent_dst
            if cat.get("sequence"):
                vals["sequence"] = cat["sequence"]
            dst_id = self._create(
                "product.public.category",
                self.dst.filter_vals("product.public.category", vals),
                cat["name"],
            )
        self.public_categ_cache[src_id] = dst_id
        return dst_id

    def map_ribbon(self, src_id):
        """Map product.ribbon by name; create with all visible attributes if missing."""
        if not src_id:
            return False
        if src_id in self.ribbon_cache:
            return self.ribbon_cache[src_id]
        # Model name varies across versions: product.ribbon (Odoo 17+) vs website_sale.ribbon.
        # The field website_ribbon_id is a Many2one whose target we read from fields_get.
        src_fields = self.src.model_fields("product.template")
        # The target model isn't directly known here; assume product.ribbon (Odoo 17+).
        ribbon_model = "product.ribbon"
        if ribbon_model not in _models_available(self.src):
            return False
        rb_fields = self.src.model_fields(ribbon_model)
        read_fields = [f for f in ("name", "html_class", "bg_color", "text_color", "position") if f in rb_fields]
        rb = self.src.read(ribbon_model, [src_id], read_fields)[0]
        ids = self.dst.search(ribbon_model, [("name", "=", rb["name"])], limit=1)
        if ids:
            dst_id = ids[0]
        else:
            vals = {"name": rb["name"]}
            for f in ("html_class", "bg_color", "text_color", "position"):
                if rb.get(f):
                    vals[f] = rb[f]
            dst_id = self._create(
                ribbon_model,
                self.dst.filter_vals(ribbon_model, vals),
                rb["name"],
            )
        self.ribbon_cache[src_id] = dst_id
        return dst_id

    def get_dynamic_clone_attribute(self, src_attr_id, src_attr_name):
        """Return a destination attribute id with create_variant='dynamic',
        cloned from the source attribute's settings. Idempotent by clone name."""
        clone_name = f"{src_attr_name} (dinamica)"
        ids = self.dst.search("product.attribute", [("name", "=", clone_name)], limit=1)
        if ids:
            return ids[0]
        attr = self.src.read("product.attribute", [src_attr_id],
                              ["display_type", "sequence"])[0]
        vals = {
            "name": clone_name,
            "create_variant": "dynamic",
            "display_type": attr.get("display_type") or "radio",
            "sequence": attr.get("sequence") or 10,
        }
        return self._create(
            "product.attribute",
            self.dst.filter_vals("product.attribute", vals),
            f"dynamic clone of '{src_attr_name}'",
        )

    def map_attribute_value_for_clone(self, src_value_id, target_attribute_id):
        """Map a source attribute value into a destination attribute (the clone)."""
        v = self.src.read("product.attribute.value", [src_value_id],
                          ["name", "sequence", "html_color", "image", "default_extra_price"])[0]
        ids = self.dst.search(
            "product.attribute.value",
            [("name", "=", v["name"]), ("attribute_id", "=", target_attribute_id)],
            limit=1,
        )
        if ids:
            return ids[0]
        vals = {
            "name": v["name"],
            "attribute_id": target_attribute_id,
            "sequence": v.get("sequence") or 10,
        }
        for opt in ("html_color", "image", "default_extra_price"):
            if v.get(opt):
                vals[opt] = v[opt]
        return self._create(
            "product.attribute.value",
            self.dst.filter_vals("product.attribute.value", vals),
            f"value '{v['name']}' for clone of attribute#{target_attribute_id}",
        )


# ---------------------------------------------------------------------------
# Variant matching by (attribute_name, value_name) set
# ---------------------------------------------------------------------------
def _ptav_key(client: OdooClient, ptav_ids):
    if not ptav_ids:
        return frozenset()
    rows = client.read(
        "product.template.attribute.value", ptav_ids,
        ["attribute_id", "product_attribute_value_id"],
    )
    return frozenset(
        (
            row["attribute_id"][1] if row["attribute_id"] else None,
            row["product_attribute_value_id"][1] if row["product_attribute_value_id"] else None,
        )
        for row in rows
    )


# ---------------------------------------------------------------------------
# Promotion
# ---------------------------------------------------------------------------
def promote_template(src, dst, mapper: Mapper, src_tmpl_id: int, log, dry_run: bool, clean: bool = False):
    src_fields = src.model_fields("product.template")
    read_fields = sorted({f for f in (TEMPLATE_SCALAR_FIELDS + TEMPLATE_REL_FIELDS) if f in src_fields})
    tmpl = src.read("product.template", [src_tmpl_id], read_fields)[0]
    log.info(f"-> template src#{src_tmpl_id} '{tmpl['name']}' (default_code={tmpl.get('default_code') or '-'})")

    # Build value dict for the destination
    vals = {}
    for f in TEMPLATE_SCALAR_FIELDS:
        if f in tmpl:
            vals[f] = tmpl[f]
    if tmpl.get("categ_id"):
        vals["categ_id"] = mapper.map_category(tmpl["categ_id"][0])
    if tmpl.get("uom_id"):
        vals["uom_id"] = mapper.map_uom(tmpl["uom_id"][0])
    if tmpl.get("uom_po_id"):
        vals["uom_po_id"] = mapper.map_uom(tmpl["uom_po_id"][0])
    if tmpl.get("product_tag_ids"):
        vals["product_tag_ids"] = [(6, 0, [mapper.map_tag(t) for t in tmpl["product_tag_ids"]])]
    if tmpl.get("public_categ_ids"):
        vals["public_categ_ids"] = [(6, 0, [mapper.map_public_category(c) for c in tmpl["public_categ_ids"]])]
    if tmpl.get("website_ribbon_id"):
        ribbon_dst = mapper.map_ribbon(tmpl["website_ribbon_id"][0])
        if ribbon_dst:
            vals["website_ribbon_id"] = ribbon_dst
    if tmpl.get("base_unit_id"):
        vals["base_unit_id"] = mapper.map_uom(tmpl["base_unit_id"][0])

    # Build attribute_line_ids commands (only used on CREATE), applying
    # per-template overrides for skipped/dynamic-cloned attributes.
    override = _TEMPLATE_OVERRIDES.get(src_tmpl_id, {})
    skip_names = override.get("skip_attribute_names", set())
    dyn_clone_names = override.get("dynamic_clone_attribute_names", set())
    attr_lines_cmds = []
    for line in src.read(
        "product.template.attribute.line",
        tmpl.get("attribute_line_ids") or [],
        ["attribute_id", "value_ids"],
    ):
        src_attr_id, src_attr_name = line["attribute_id"]
        if src_attr_name in skip_names:
            log.info(f"  -- override: skipping attribute '{src_attr_name}' for src#{src_tmpl_id}")
            continue
        if src_attr_name in dyn_clone_names:
            dst_attr = mapper.get_dynamic_clone_attribute(src_attr_id, src_attr_name)
            dst_vals = [mapper.map_attribute_value_for_clone(v, dst_attr) for v in line["value_ids"]]
            log.info(f"  -- override: using dynamic clone for '{src_attr_name}' "
                     f"(src#{src_tmpl_id}) -> dst_attr#{dst_attr}")
        else:
            dst_attr = mapper.map_attribute(src_attr_id)
            dst_vals = [mapper.map_attribute_value(v) for v in line["value_ids"]]
        attr_lines_cmds.append((0, 0, {
            "attribute_id": dst_attr,
            "value_ids": [(6, 0, dst_vals)],
        }))

    # Idempotent lookup in destination (skipped in --clean mode: always CREATE).
    if clean:
        # Resume guard: if a previous --clean run already created a dst template
        # for this src_id and it's still ACTIVE, skip to avoid duplicates.
        already_active = _xid_points_to_active(dst, src_tmpl_id)
        if already_active:
            log.info(f"  [clean/resume] already promoted: dst#{already_active} is active; skipping")
            mapper.template_map[src_tmpl_id] = already_active
            # Still rebuild variant_map so cross-sells/accessories work in 2nd pass
            _rebuild_variant_map(src, dst, mapper, tmpl, already_active, log)
            return
        target_tmpl_id = None
        # Remove stale __promote__ XID (points to archived) so the new create can register its own.
        _drop_stale_promote_xid(dst, src_tmpl_id, log, dry_run)
    else:
        target_tmpl_id = _find_target_template(dst, tmpl, src_tmpl_id, log)

    safe_vals = dst.filter_vals("product.template", vals)
    if target_tmpl_id:
        log.info(f"  ~ UPDATE dst#{target_tmpl_id} (attribute_line_ids preserved)")
        if not dry_run:
            dst.write("product.template", [target_tmpl_id], safe_vals)
            # If this match was via default_code (no XID yet), set the XID so
            # future runs/probes recognize it as already promoted.
            existing_xid = dst.search(
                "ir.model.data",
                [("module", "=", "__promote__"),
                 ("name", "=", f"tmpl_{src_tmpl_id}"),
                 ("model", "=", "product.template")],
                limit=1,
            )
            if not existing_xid:
                _set_promote_xid(dst, target_tmpl_id, src_tmpl_id, log)
    else:
        if attr_lines_cmds:
            safe_vals["attribute_line_ids"] = attr_lines_cmds
        log.info(f"  + CREATE template ({len(attr_lines_cmds)} attribute line(s))")
        if dry_run:
            log.info(f"    [DRY] vals keys: {list(safe_vals.keys())}")
            return
        target_tmpl_id = dst.create("product.template", safe_vals)
        log.info(f"    + created dst#{target_tmpl_id}")
        _set_promote_xid(dst, target_tmpl_id, src_tmpl_id, log)

    mapper.template_map[src_tmpl_id] = target_tmpl_id

    _ensure_dynamic_variants(src, dst, mapper, tmpl, target_tmpl_id, log, dry_run)
    _promote_variants(src, dst, mapper, tmpl, target_tmpl_id, log, dry_run)
    _promote_template_images(src, dst, tmpl, target_tmpl_id, log, dry_run)
    _promote_documents(src, dst, mapper, tmpl, target_tmpl_id, log, dry_run)


def _find_target_template(dst: OdooClient, src_tmpl: dict, src_tmpl_id: int, log):
    """Return dst template id by default_code, then by __promote__.tmpl_<src_id> XID."""
    code = src_tmpl.get("default_code")
    if code:
        existing = dst.search("product.template", [("default_code", "=", code)], limit=1)
        if existing:
            log.info(f"  ~ matched by default_code='{code}' -> dst#{existing[0]}")
            return existing[0]
    imd = dst.search_read(
        "ir.model.data",
        [("module", "=", "__promote__"), ("name", "=", f"tmpl_{src_tmpl_id}"),
         ("model", "=", "product.template")],
        ["res_id"], limit=1,
    )
    if imd:
        log.info(f"  ~ matched by xid __promote__.tmpl_{src_tmpl_id} -> dst#{imd[0]['res_id']}")
        return imd[0]["res_id"]
    return None


def _set_promote_xid(dst: OdooClient, dst_tmpl_id: int, src_tmpl_id: int, log):
    try:
        dst.create("ir.model.data", {
            "module": "__promote__",
            "name": f"tmpl_{src_tmpl_id}",
            "model": "product.template",
            "res_id": dst_tmpl_id,
            "noupdate": True,
        })
    except Exception as exc:
        log.warning(f"    could not set xid __promote__.tmpl_{src_tmpl_id}: {exc}")


def _xid_points_to_active(dst: OdooClient, src_tmpl_id: int):
    """If __promote__.tmpl_<src_id> exists AND points to an active template,
    return that dst template id. Otherwise return None."""
    rows = dst.search_read(
        "ir.model.data",
        [("module", "=", "__promote__"),
         ("name", "=", f"tmpl_{src_tmpl_id}"),
         ("model", "=", "product.template")],
        ["res_id"], limit=1,
    )
    if not rows:
        return None
    dst_tmpl_id = rows[0]["res_id"]
    rec = dst.read("product.template", [dst_tmpl_id], ["active"])
    if rec and rec[0].get("active"):
        return dst_tmpl_id
    return None


def _rebuild_variant_map(src, dst, mapper: Mapper, src_tmpl, dst_tmpl_id, log):
    """Populate mapper.variant_map for an already-promoted template, so the
    2nd-pass cross-sells / accessories can still resolve src variant ids."""
    src_variant_ids = src_tmpl.get("product_variant_ids") or []
    if not src_variant_ids:
        return
    src_variants = src.read(
        "product.product", src_variant_ids, ["product_template_attribute_value_ids"],
    )
    dst_variants = dst.search_read(
        "product.product",
        [("product_tmpl_id", "=", dst_tmpl_id)],
        ["id", "product_template_attribute_value_ids"],
    )
    dst_key_to_id = {
        _ptav_key(dst, v["product_template_attribute_value_ids"]): v["id"]
        for v in dst_variants
    }
    matched = 0
    for sv in src_variants:
        key = _ptav_key(src, sv["product_template_attribute_value_ids"])
        dst_id = dst_key_to_id.get(key)
        if dst_id:
            mapper.variant_map[sv["id"]] = dst_id
            matched += 1
    log.info(f"    [clean/resume] re-mapped {matched}/{len(src_variants)} variants for dst#{dst_tmpl_id}")


def _drop_stale_promote_xid(dst: OdooClient, src_tmpl_id: int, log, dry_run: bool):
    """Delete an existing ir.model.data row for __promote__.tmpl_<src_id> so the
    fresh create can register its own. Used only in --clean mode where the
    pre-existing XID is expected to point to an archived (orphaned) template."""
    existing = dst.search(
        "ir.model.data",
        [("module", "=", "__promote__"),
         ("name", "=", f"tmpl_{src_tmpl_id}"),
         ("model", "=", "product.template")],
    )
    if not existing:
        return
    log.info(f"  [clean] removing stale XID __promote__.tmpl_{src_tmpl_id} (rows={existing})")
    if not dry_run:
        try:
            dst.unlink("ir.model.data", existing)
        except Exception as exc:
            log.warning(f"    could not unlink stale XID: {exc}")


def _ensure_dynamic_variants(src, dst, mapper: Mapper, src_tmpl, target_tmpl_id, log, dry_run):
    """For templates whose attribute_line_ids contain dynamic-variant attributes,
    Odoo does NOT auto-generate variants on the destination when we set
    attribute_line_ids. We have to create the same combinations explicitly.

    Reads source variants and for each one looks up the dst combination of
    product.template.attribute.value ids that matches the source variant's
    (attribute_name, value_name) signature. If no dst variant exists with
    that combination yet, calls _create_product_variant on the template.
    """
    if dry_run:
        return
    src_lines = src.read(
        "product.template.attribute.line",
        src_tmpl.get("attribute_line_ids") or [],
        ["attribute_id"],
    )
    src_attr_ids = [ln["attribute_id"][0] for ln in src_lines if ln.get("attribute_id")]
    if not src_attr_ids:
        return
    src_attrs = src.read("product.attribute", src_attr_ids, ["create_variant"])
    has_dynamic = any(a.get("create_variant") == "dynamic" for a in src_attrs)
    if not has_dynamic:
        return

    log.info(f"  [dyn] template has dynamic attribute(s); creating missing variants explicitly")

    src_variant_ids = src_tmpl.get("product_variant_ids") or []
    if not src_variant_ids:
        return

    src_variants = src.read(
        "product.product", src_variant_ids,
        ["product_template_attribute_value_ids"],
    )

    # Build dst ptav lookup: (attribute_name, value_name) -> dst ptav id
    dst_ptavs = dst.search_read(
        "product.template.attribute.value",
        [("product_tmpl_id", "=", target_tmpl_id)],
        ["id", "attribute_id", "product_attribute_value_id"],
    )
    dst_ptav_by_key = {}
    for r in dst_ptavs:
        if r["attribute_id"] and r["product_attribute_value_id"]:
            key = (r["attribute_id"][1], r["product_attribute_value_id"][1])
            dst_ptav_by_key[key] = r["id"]

    # Existing dst variants by ptav signature
    dst_variants_existing = dst.search_read(
        "product.product",
        [("product_tmpl_id", "=", target_tmpl_id)],
        ["id", "product_template_attribute_value_ids"],
    )
    existing_keys = {
        _ptav_key(dst, v["product_template_attribute_value_ids"]): v["id"]
        for v in dst_variants_existing
    }

    created = 0
    for sv in src_variants:
        src_key = _ptav_key(src, sv["product_template_attribute_value_ids"])
        if not src_key:
            continue
        if src_key in existing_keys:
            continue
        # Translate src ptavs to dst ptav ids using (attribute_name, value_name)
        dst_ptav_ids = []
        missing = False
        for attr_name, val_name in src_key:
            dst_ptav = dst_ptav_by_key.get((attr_name, val_name))
            if not dst_ptav:
                log.warning(
                    f"    [dyn] cannot map ptav (attr='{attr_name}', val='{val_name}') for "
                    f"src variant; skipping"
                )
                missing = True
                break
            dst_ptav_ids.append(dst_ptav)
        if missing:
            continue
        try:
            new_id = dst.create("product.product", {
                "product_tmpl_id": target_tmpl_id,
                "product_template_attribute_value_ids": [(6, 0, dst_ptav_ids)],
            })
            if new_id:
                created += 1
                log.info(f"    [dyn] created dynamic variant dst#{new_id} for {set(src_key)}")
        except Exception as exc:
            log.warning(f"    [dyn] could not create variant for {set(src_key)}: {exc}")
    if created:
        log.info(f"  [dyn] created {created} dynamic variant(s) on dst#{target_tmpl_id}")


def _promote_cross_sells(src, dst, mapper: Mapper, src_tmpl_id: int, log, dry_run: bool):
    """Second-pass write of cross-sell relations now that every template exists in dst.

    Three relations:
    - alternative_product_ids: M2M to product.template (symmetric)
    - optional_product_ids: M2M to product.template
    - accessory_product_ids: M2M to product.product (variant-level)
    """
    src_fields = src.model_fields("product.template")
    read_fields = [f for f in CROSS_SELL_TEMPLATE_FIELDS if f in src_fields]
    if not read_fields:
        return
    tmpl = src.read("product.template", [src_tmpl_id], read_fields)[0]
    dst_tmpl_id = mapper.template_map.get(src_tmpl_id)
    if not dst_tmpl_id:
        log.warning(f"  ! cross-sells: src#{src_tmpl_id} has no dst mapping; skipped")
        return

    vals = {}
    for f in ("alternative_product_ids", "optional_product_ids"):
        if f not in tmpl:
            continue
        src_refs = tmpl.get(f) or []
        if not src_refs:
            continue
        dst_refs = [mapper.template_map[s] for s in src_refs if s in mapper.template_map]
        missing = len(src_refs) - len(dst_refs)
        if missing:
            log.warning(f"  ! {f} src#{src_tmpl_id}: {missing} ref(s) not in template_map; partial")
        if dst_refs:
            vals[f] = [(6, 0, dst_refs)]
    if "accessory_product_ids" in tmpl:
        src_var_refs = tmpl.get("accessory_product_ids") or []
        if src_var_refs:
            dst_var_refs = [mapper.variant_map[s] for s in src_var_refs if s in mapper.variant_map]
            missing = len(src_var_refs) - len(dst_var_refs)
            if missing:
                log.warning(
                    f"  ! accessory_product_ids src#{src_tmpl_id}: {missing} variant ref(s) "
                    f"not in variant_map; partial"
                )
            if dst_var_refs:
                vals["accessory_product_ids"] = [(6, 0, dst_var_refs)]

    if not vals:
        return
    safe_vals = dst.filter_vals("product.template", vals)
    if not safe_vals:
        return
    log.info(f"  ~ cross-sells dst#{dst_tmpl_id}: writing {list(safe_vals.keys())}")
    if not dry_run:
        dst.write("product.template", [dst_tmpl_id], safe_vals)


def _promote_variants(src, dst, mapper: Mapper, src_tmpl, target_tmpl_id, log, dry_run):
    src_variant_ids = src_tmpl.get("product_variant_ids") or []
    if not src_variant_ids:
        return
    src_pp_fields = src.model_fields("product.product")
    fields = [f for f in VARIANT_FIELDS if f in src_pp_fields]
    fields.append("product_template_attribute_value_ids")
    src_variants = src.read("product.product", src_variant_ids, list(set(fields)))

    dst_variants = dst.search_read(
        "product.product",
        [("product_tmpl_id", "=", target_tmpl_id)],
        ["product_template_attribute_value_ids"],
    )
    dst_key_to_id = {
        _ptav_key(dst, v["product_template_attribute_value_ids"]): v["id"]
        for v in dst_variants
    }

    for sv in src_variants:
        key = _ptav_key(src, sv["product_template_attribute_value_ids"])
        dst_id = dst_key_to_id.get(key)
        if not dst_id:
            log.warning(f"  ! variant src#{sv['id']} key={set(key) or '{}'} not found in dst -- skipped")
            continue
        mapper.variant_map[sv["id"]] = dst_id
        vals = {f: sv[f] for f in VARIANT_FIELDS if f in sv}
        safe_vals = dst.filter_vals("product.product", vals)
        if not safe_vals:
            continue
        log.info(f"  ~ variant src#{sv['id']} -> dst#{dst_id}: write {list(safe_vals.keys())}")
        if not dry_run:
            dst.write("product.product", [dst_id], safe_vals)
        _promote_variant_images(src, dst, sv, dst_id, target_tmpl_id, log, dry_run)


def _promote_template_images(src, dst, src_tmpl, target_tmpl_id, log, dry_run):
    if "product_template_image_ids" not in src.model_fields("product.template"):
        return
    img_ids = src_tmpl.get("product_template_image_ids") or []
    if not img_ids:
        return
    images = src.read("product.image", img_ids, IMAGE_FIELDS)
    # Replace strategy: clear existing template-level extras, then re-create
    existing = dst.search(
        "product.image",
        [("product_tmpl_id", "=", target_tmpl_id), ("product_variant_id", "=", False)],
    )
    if existing and not dry_run:
        dst.unlink("product.image", existing)
    for im in images:
        vals = {
            "name": im["name"],
            "image_1920": im["image_1920"],
            "sequence": im.get("sequence") or 10,
            "product_tmpl_id": target_tmpl_id,
        }
        log.info(f"  + product.image (template) '{im['name']}'")
        if not dry_run:
            dst.create("product.image", dst.filter_vals("product.image", vals))


def _promote_variant_images(src, dst, src_variant, target_variant_id, target_tmpl_id, log, dry_run):
    img_ids = src.search("product.image", [("product_variant_id", "=", src_variant["id"])])
    if not img_ids:
        return
    images = src.read("product.image", img_ids, IMAGE_FIELDS)
    existing = dst.search("product.image", [("product_variant_id", "=", target_variant_id)])
    if existing and not dry_run:
        dst.unlink("product.image", existing)
    for im in images:
        vals = {
            "name": im["name"],
            "image_1920": im["image_1920"],
            "sequence": im.get("sequence") or 10,
            "product_tmpl_id": target_tmpl_id,
            "product_variant_id": target_variant_id,
        }
        log.info(f"  + product.image (variant#{target_variant_id}) '{im['name']}'")
        if not dry_run:
            dst.create("product.image", dst.filter_vals("product.image", vals))


def _promote_documents(src, dst, mapper: Mapper, src_tmpl, target_tmpl_id, log, dry_run):
    """Copy `product.document` records; per-doc try/except + oversize skip."""
    if "product.document" not in _models_available(dst):
        log.info("  (product.document not present in dst -- skipping documents)")
        return
    src_variant_ids = src_tmpl.get("product_variant_ids") or []
    domain = [
        "|",
        "&", ("res_model", "=", "product.template"), ("res_id", "=", src_tmpl["id"]),
        "&", ("res_model", "=", "product.product"),
              ("res_id", "in", src_variant_ids or [0]),
    ]
    doc_ids = src.search("product.document", domain)
    if not doc_ids:
        return
    src_doc_fields = src.model_fields("product.document")
    # Read metadata only first (no `datas`) to size-check before transferring binaries.
    meta_fields = [f for f in DOCUMENT_FIELDS if f in src_doc_fields and f != "datas"]
    if "file_size" in src_doc_fields and "file_size" not in meta_fields:
        meta_fields.append("file_size")
    metas = src.read("product.document", doc_ids, meta_fields)

    for meta in metas:
        if meta["res_model"] == "product.template":
            target_res_id = target_tmpl_id
        elif meta["res_model"] == "product.product":
            target_res_id = mapper.variant_map.get(meta["res_id"])
            if not target_res_id:
                log.warning(f"  ! document src#{meta['id']} variant {meta['res_id']} not mapped -- skipped")
                continue
        else:
            continue
        dup = dst.search("product.document", [
            ("name", "=", meta["name"]),
            ("res_model", "=", meta["res_model"]),
            ("res_id", "=", target_res_id),
        ], limit=1)
        if dup:
            log.info(f"  ~ document '{meta['name']}' already on {meta['res_model']}#{target_res_id} -- skipped")
            continue
        size = meta.get("file_size") or 0
        if size and size > _MAX_DOC_BYTES:
            log.warning(
                f"  ! document src#{meta['id']} '{meta['name']}' is "
                f"{size/1024/1024:.1f} MB > {_MAX_DOC_BYTES/1024/1024:.0f} MB -- "
                f"SKIPPED, attach manually in Production on {meta['res_model']}#{target_res_id}"
            )
            continue
        # Read the full record including datas only when we're going to upload.
        read_doc_fields = [f for f in DOCUMENT_FIELDS if f in src_doc_fields]
        full = src.read("product.document", [meta["id"]], read_doc_fields)[0]
        vals = {k: full[k] for k in read_doc_fields if k != "id"}
        vals["res_id"] = target_res_id
        safe_vals = dst.filter_vals("product.document", vals)
        log.info(f"  + document '{meta['name']}' ({size/1024:.0f} KB) on {meta['res_model']}#{target_res_id}")
        if dry_run:
            continue
        try:
            dst.create("product.document", safe_vals)
        except Exception as exc:
            log.warning(f"  ! document src#{meta['id']} '{meta['name']}' create failed: {exc} -- skipped")


def _models_available(client: OdooClient):
    """Return the set of installed model names on the client (cached on the client)."""
    cache_key = "_models_set"
    if not hasattr(client, cache_key):
        rows = client.search_read("ir.model", [], ["model"])
        setattr(client, cache_key, {r["model"] for r in rows})
    return getattr(client, cache_key)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def collect_template_ids(src: OdooClient, args, log):
    if args.ids:
        return [int(x) for x in args.ids.split(",") if x.strip()]
    if args.ids_file:
        text = Path(args.ids_file).read_text(encoding="utf-8")
        # accept comma- or whitespace-separated ints
        toks = [t for t in text.replace(",", " ").split() if t]
        return [int(t) for t in toks]
    if args.codes:
        codes = [c.strip() for c in args.codes.split(",") if c.strip()]
        ids = src.search("product.template", [("default_code", "in", codes)])
        log.info(f"resolved {len(ids)} templates from {len(codes)} default_codes")
        return ids
    if args.domain:
        domain = json.loads(args.domain)
        ids = src.search("product.template", domain)
        log.info(f"resolved {len(ids)} templates from domain {domain}")
        return ids
    raise SystemExit("specify --ids, --codes or --domain")


def main():
    parser = argparse.ArgumentParser(description="Promote products Staging->Production (Odoo 19)")
    parser.add_argument("--env", help="path to .env file with SRC_*/DST_* vars")
    sel = parser.add_mutually_exclusive_group(required=True)
    sel.add_argument("--ids", help="comma-separated product.template ids in source DB")
    sel.add_argument("--ids-file", dest="ids_file", help="path to a file with template ids (comma- or whitespace-separated)")
    sel.add_argument("--codes", help="comma-separated default_code values")
    sel.add_argument("--domain", help="JSON domain on product.template")
    parser.add_argument("--dry-run", action="store_true", help="no writes to destination")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument(
        "--clean",
        action="store_true",
        help="force CREATE every template: skip default_code + __promote__ XID matches, "
             "delete stale __promote__ XIDs first. Use this for a fresh-from-zero "
             "re-promotion after archiving the previous batch in dst.",
    )
    parser.add_argument(
        "--skip-cross-sells",
        action="store_true",
        help="skip the second pass that writes alternative/optional/accessory product references",
    )
    args = parser.parse_args()

    log = setup_logging(args.verbose)
    load_env(args.env)

    required = ["SRC_URL", "SRC_DB", "SRC_LOGIN", "SRC_API_KEY",
                "DST_URL", "DST_DB", "DST_LOGIN", "DST_API_KEY"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        raise SystemExit(f"missing env vars: {missing}")

    src = OdooClient(os.environ["SRC_URL"], os.environ["SRC_DB"],
                     os.environ["SRC_LOGIN"], os.environ["SRC_API_KEY"], "SRC", log)
    dst = OdooClient(os.environ["DST_URL"], os.environ["DST_DB"],
                     os.environ["DST_LOGIN"], os.environ["DST_API_KEY"], "DST", log)

    if args.dry_run:
        log.info("=== DRY RUN -- destination will not be modified ===")
    if args.clean:
        log.info("=== CLEAN MODE -- forcing CREATE, stale XIDs will be dropped ===")

    mapper = Mapper(src, dst, log, args.dry_run)
    src_tmpl_ids = collect_template_ids(src, args, log)
    log.info(f"selected {len(src_tmpl_ids)} template(s) to promote")

    ok = ko = 0
    for i, tid in enumerate(src_tmpl_ids, 1):
        log.info(f"--- [{i}/{len(src_tmpl_ids)}] ---")
        try:
            promote_template(src, dst, mapper, tid, log, args.dry_run, clean=args.clean)
            ok += 1
        except Exception as exc:
            log.exception(f"FAILED template src#{tid}: {exc}")
            ko += 1

    if not args.skip_cross_sells:
        log.info(f"=== 2nd pass: cross-sell relations ({len(mapper.template_map)} mapped templates) ===")
        for i, tid in enumerate(src_tmpl_ids, 1):
            if tid not in mapper.template_map:
                continue
            try:
                _promote_cross_sells(src, dst, mapper, tid, log, args.dry_run)
            except Exception as exc:
                log.warning(f"  ! cross-sells failed for src#{tid}: {exc}")

    log.info(f"=== done: ok={ok} failed={ko} ===")
    sys.exit(0 if ko == 0 else 1)


if __name__ == "__main__":
    main()
