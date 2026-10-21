# Supplier Adapter Guide

Use this when adding a new supplier to `hiper_sync`.

## 1. Pick the source type

- `ftp_csv`: supplier gives FTP host/user/password and a file path
- `csv_url`: supplier gives a direct CSV URL
- `json_url`: supplier gives an API endpoint
- `crawler_csv`: only for legacy local crawler flows
- `local_csv`: local file import for testing

## 2. Add the vendor record

Seed it in:

- `hiper_sync/data/vendor_data.xml`

Set:

- `name`
- `code`
- `source_kind`
- connection fields such as `feed_url`, `api_url_template`, `ftp_host`, `remote_filename`

## 3. Add an adapter class

Create a new adapter in:

- `hiper_sync/services/vendor_adapters.py`

Typical structure:

```python
class IntExampleAdapter(SharedSupplierAdapter):
    def validate_configuration(self):
        missing = []
        if not self.vendor.feed_url:
            missing.append("feed_url")
        return missing

    def fetch_rows(self):
        return self.fetch_csv_from_url(self.vendor.feed_url, delimiter=";")

    def normalize_row(self, row):
        values = {
            "name_pt": row.get("Name"),
            "reference": row.get("Reference"),
            "ean13": row.get("EAN"),
            "brand": row.get("Brand"),
            "category": row.get("Category"),
            "sub_category": row.get("SubCategory"),
            "description_pt": row.get("Description"),
            "description_short_pt": row.get("ShortDescription"),
            "images": ensure_list(row.get("Image")),
            "unit_price": parse_float(row.get("Price")),
            "wholesale_price": parse_float(row.get("Cost")),
            "quantity": parse_int(row.get("Stock")),
        }
        return self.apply_common(values) if is_valid_ean13(values["ean13"]) else False
```

## 4. Register the adapter

Add the adapter to the registry in:

- `hiper_sync/services/vendor_adapters.py`

Map the supplier code to the adapter class.

## 5. Use the normalized schema

The publisher expects these normalized keys when available:

- `name_pt`
- `reference`
- `ean13`
- `brand`
- `category`
- `sub_category`
- `description_pt`
- `description_short_pt`
- `images`
- `unit_price`
- `wholesale_price`
- `quantity`
- `features`
- `weight`
- `volume`
- `tags`
- `info_manual`

## 6. First debugging pass

Use `Fetch Preview` first.

The sync message now tells you:

- raw row count
- normalized row count
- dropped row count
- invalid/missing EAN count
- missing name/reference count
- sample keys from the first raw row
- a short first-row preview

This is the fastest way to discover field-name mismatches.

## 7. Category behavior

- Explicit `Category Maps` win first.
- If there is no map, supplier categories are auto-created under `Default Internal Category`.
- Website categories are auto-created under `Default Website Category`, or at root if no website default is set.

## 8. Important rule

Most suppliers in this project are EAN-driven.

If `ean13` is missing or not 13 digits, the row is usually dropped on purpose to match the old Prestashop behavior.
