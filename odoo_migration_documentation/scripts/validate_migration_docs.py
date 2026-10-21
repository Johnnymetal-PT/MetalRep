#!/usr/bin/env python3
"""Validate structured migration documentation."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "migration-docs"
JSONL = DOCS / "migration_errors.jsonl"
ROOT_CAUSES = DOCS / "root_causes.json"

REQUIRED_FIELDS = [
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
    "severity",
    "status",
    "root_cause_status",
    "technical_signature",
    "tags",
    "evidence",
    "recommended_next_action",
]

PHASES = {
    "Preparação ambiente",
    "Arranque servidor",
    "Carregamento registry",
    "Instalação módulo",
    "Atualização módulo",
    "Migração de dados",
    "Carregamento XML/CSV",
    "Teste funcional",
    "Relatórios",
    "Frontend/Assets",
    "Integração externa",
    "Performance",
    "Validação contabilística/fiscal",
}

TECHNICAL_LAYERS = {
    "Manifest/Dependências",
    "Python/ORM",
    "Modelo/Campo removido",
    "Assinatura de método",
    "XML/View/XPath",
    "Security/ACL/Rules",
    "Dados/Constraints",
    "XML ID/Noupdate",
    "QWeb/Reports",
    "JS/OWL/Assets",
    "SQL",
    "Integração/API",
    "Performance",
    "Lógica funcional",
}

SEVERITIES = {
    "S1 - Bloqueante",
    "S2 - Alta",
    "S3 - Média",
    "S4 - Baixa",
    "S5 - Observação",
}

STATUSES = {
    "Novo",
    "Em triagem",
    "Reproduzido",
    "Causa identificada",
    "Correção em curso",
    "Corrigido",
    "Reteste falhou",
    "Retestado OK",
    "Fechado",
    "Duplicado",
    "Não aplicável",
}

ROOT_CAUSE_STATUSES = {"confirmed", "probable", "unknown", "not_applicable"}


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.exists():
        return rows
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON at {path}:{line_number}: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"Line {line_number} must be a JSON object")
        rows.append(value)
    return rows


def load_root_causes() -> list[dict]:
    if not ROOT_CAUSES.exists():
        return []
    value = json.loads(ROOT_CAUSES.read_text(encoding="utf-8") or "[]")
    if not isinstance(value, list):
        raise ValueError("root_causes.json must contain a list")
    return value


def main() -> int:
    errors: list[str] = []

    rows = load_jsonl(JSONL)
    root_causes = load_root_causes()
    root_cause_ids = {rc.get("root_cause_id") for rc in root_causes if isinstance(rc, dict)}
    error_ids: set[str] = set()

    for index, row in enumerate(rows, start=1):
        prefix = f"row {index}"

        for field in REQUIRED_FIELDS:
            if field not in row:
                errors.append(f"{prefix}: missing required field {field}")

        error_id = row.get("error_id", "")
        if not re.fullmatch(r"MIG-\d{4}", str(error_id)):
            errors.append(f"{prefix}: invalid error_id {error_id!r}")
        if error_id in error_ids:
            errors.append(f"{prefix}: duplicated error_id {error_id}")
        error_ids.add(str(error_id))

        run_id = row.get("run_id", "")
        if run_id and not re.fullmatch(r"RUN-\d{4}-\d{2}-\d{2}-\d{2}", str(run_id)):
            errors.append(f"{prefix}: invalid run_id {run_id!r}")

        phase = row.get("phase", "")
        if phase and phase not in PHASES:
            errors.append(f"{prefix}: invalid phase {phase!r}")

        technical_layer = row.get("technical_layer", "")
        if technical_layer and technical_layer not in TECHNICAL_LAYERS:
            errors.append(f"{prefix}: invalid technical_layer {technical_layer!r}")

        severity = row.get("severity", "")
        if severity and severity not in SEVERITIES:
            errors.append(f"{prefix}: invalid severity {severity!r}")

        status = row.get("status", "")
        if status and status not in STATUSES:
            errors.append(f"{prefix}: invalid status {status!r}")

        root_cause_status = row.get("root_cause_status", "")
        if root_cause_status and root_cause_status not in ROOT_CAUSE_STATUSES:
            errors.append(f"{prefix}: invalid root_cause_status {root_cause_status!r}")

        duplicate_of = row.get("duplicate_of", "")
        if duplicate_of and not re.fullmatch(r"MIG-\d{4}", str(duplicate_of)):
            errors.append(f"{prefix}: invalid duplicate_of {duplicate_of!r}")

        root_cause_id = row.get("root_cause_id", "")
        if root_cause_id:
            if not re.fullmatch(r"RC-\d{4}", str(root_cause_id)):
                errors.append(f"{prefix}: invalid root_cause_id {root_cause_id!r}")
            elif root_cause_ids and root_cause_id not in root_cause_ids:
                errors.append(f"{prefix}: root_cause_id {root_cause_id} not found in root_causes.json")

        if severity in {"S1 - Bloqueante", "S2 - Alta"}:
            detail_file = DOCS / "errors" / f"{error_id}.md"
            if error_id and not detail_file.exists():
                errors.append(f"{prefix}: {severity} requires detail page {detail_file}")

    for rc_index, rc in enumerate(root_causes, start=1):
        if not isinstance(rc, dict):
            errors.append(f"root cause {rc_index}: must be an object")
            continue
        rc_id = rc.get("root_cause_id", "")
        if not re.fullmatch(r"RC-\d{4}", str(rc_id)):
            errors.append(f"root cause {rc_index}: invalid root_cause_id {rc_id!r}")
        related_errors = rc.get("related_errors", [])
        if related_errors and not isinstance(related_errors, list):
            errors.append(f"root cause {rc_id}: related_errors must be a list")

    if errors:
        print("Migration documentation validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Migration documentation validation OK ({len(rows)} errors, {len(root_causes)} root causes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
