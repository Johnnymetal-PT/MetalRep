#!/usr/bin/env python3
"""Sync migration-docs/migration_errors.csv from migration_errors.jsonl."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSONL = ROOT / "migration-docs" / "migration_errors.jsonl"
CSV = ROOT / "migration-docs" / "migration_errors.csv"

FIELDS = [
    "error_id",
    "run_id",
    "timestamp",
    "source",
    "odoo_source_version",
    "odoo_target_version",
    "phase",
    "custom_module",
    "standard_module",
    "functional_area",
    "technical_layer",
    "error_type",
    "short_summary",
    "main_error_message",
    "affected_file",
    "affected_model",
    "affected_field",
    "affected_xml_id",
    "severity",
    "status",
    "root_cause_id",
    "root_cause_summary",
    "root_cause_status",
    "technical_signature",
    "duplicate_of",
    "tags",
    "recommended_next_action",
]


def load_rows() -> list[dict]:
    rows: list[dict] = []
    if not JSONL.exists():
        return rows
    for line_number, line in enumerate(JSONL.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid JSON on {JSONL}:{line_number}: {exc}") from exc
        rows.append(row)
    return rows


def flatten_value(value):
    if isinstance(value, list):
        return ";".join(str(v) for v in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    if value is None:
        return ""
    return str(value)


def main() -> None:
    rows = load_rows()
    CSV.parent.mkdir(parents=True, exist_ok=True)
    with CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: flatten_value(row.get(field, "")) for field in FIELDS})
    print(f"Wrote {CSV} with {len(rows)} rows")


if __name__ == "__main__":
    main()
