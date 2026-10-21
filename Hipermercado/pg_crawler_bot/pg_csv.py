from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable


PG_CSV_COLUMNS = [
    "source_url",
    "name",
    "reference",
    "ean13",
    "brand",
    "category",
    "sub_category",
    "unit_price",
    "quantity",
    "availability_text",
    "image_url",
    "thumbnail_url",
    "images",
    "extra_media_json",
    "description",
    "description_short",
    "features_json",
]


def pg_write_csv(records: Iterable[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PG_CSV_COLUMNS)
        writer.writeheader()
        for record in records:
            row = {}
            for column in PG_CSV_COLUMNS:
                value = record.get(column)
                if isinstance(value, list) and column.endswith("_json"):
                    row[column] = json.dumps(value, ensure_ascii=False, sort_keys=True)
                elif isinstance(value, list):
                    row[column] = ",".join(str(item) for item in value if item)
                elif isinstance(value, dict):
                    row[column] = json.dumps(value, ensure_ascii=False, sort_keys=True)
                elif value is None:
                    row[column] = ""
                else:
                    row[column] = str(value)
            writer.writerow(row)
