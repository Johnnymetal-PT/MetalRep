"""Inspect fields of key models on SRC to detect v19 renames/removals."""
import os, xmlrpc.client
from pathlib import Path

env = Path(__file__).with_name(".promote.env")
for raw in env.read_text(encoding="utf-8").splitlines():
    line = raw.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

url = os.environ["SRC_URL"].rstrip("/")
db = os.environ["SRC_DB"]; login = os.environ["SRC_LOGIN"]; key = os.environ["SRC_API_KEY"]
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
uid = common.authenticate(db, login, key, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

CANDIDATES_BY_MODEL = {
    "product.template": [
        "name", "default_code", "barcode", "active", "sale_ok", "purchase_ok", "is_published",
        "list_price", "standard_price",
        "description", "description_sale", "description_purchase",
        "description_ecommerce", "public_description",
        "weight", "volume", "image_1920",
        "type", "is_storable", "detailed_type",
        "tracking", "invoice_policy", "service_type", "service_tracking",
        "categ_id", "uom_id", "uom_po_id", "product_tag_ids",
        "attribute_line_ids", "product_variant_ids",
        "product_template_image_ids", "product_document_ids",
        "website_sequence", "website_size_x", "website_size_y",
        "allow_out_of_stock_order", "show_availability", "available_threshold",
    ],
    "product.product": [
        "default_code", "barcode", "active",
        "lst_price", "list_price", "standard_price",
        "weight", "volume",
        "image_variant_1920",
        "product_template_attribute_value_ids",
        "product_variant_image_ids",
        "product_document_ids",
    ],
    "product.attribute": [
        "name", "create_variant", "display_type", "sequence",
    ],
    "product.attribute.value": [
        "name", "attribute_id", "sequence", "html_color", "image", "default_extra_price",
    ],
    "product.image": [
        "name", "image_1920", "sequence", "product_tmpl_id", "product_variant_id",
    ],
    "product.document": [
        "name", "datas", "mimetype", "type", "url",
        "res_model", "res_id",
        "shown_on_product_page", "attached_on_mobile", "attached_on",
    ],
}

for model, candidates in CANDIDATES_BY_MODEL.items():
    fields = models.execute_kw(db, uid, key, model, "fields_get", [], {"attributes": ["type"]})
    have = set(fields)
    missing = [c for c in candidates if c not in have]
    print(f"{model}: missing -> {missing}")
