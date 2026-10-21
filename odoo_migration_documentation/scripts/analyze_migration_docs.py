#!/usr/bin/env python3
"""Generate a simple overall summary from migration_errors.jsonl."""

from __future__ import annotations

import collections
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "migration-docs"
JSONL = DOCS / "migration_errors.jsonl"
SUMMARY = DOCS / "overall-summary.md"


def load_rows() -> list[dict]:
    if not JSONL.exists():
        return []
    rows: list[dict] = []
    for line in JSONL.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def section(title: str, counter: collections.Counter) -> str:
    lines = [f"## {title}", ""]
    if not counter:
        lines.append("Sem dados.")
    else:
        for key, count in counter.most_common():
            label = key or "(vazio)"
            lines.append(f"- {label}: {count}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    rows = load_rows()
    by_severity = collections.Counter(row.get("severity", "") for row in rows)
    by_layer = collections.Counter(row.get("technical_layer", "") for row in rows)
    by_module = collections.Counter(row.get("custom_module", "") for row in rows)
    by_phase = collections.Counter(row.get("phase", "") for row in rows)
    by_root_cause = collections.Counter(row.get("root_cause_id", "") for row in rows if row.get("root_cause_id"))

    content = [
        "# Overall migration summary",
        "",
        f"Total documented errors: {len(rows)}",
        "",
        section("By severity", by_severity),
        section("By technical layer", by_layer),
        section("By custom module", by_module),
        section("By phase", by_phase),
        section("By root cause", by_root_cause),
    ]
    SUMMARY.write_text("\n".join(content), encoding="utf-8")
    print(f"Wrote {SUMMARY}")


if __name__ == "__main__":
    main()
