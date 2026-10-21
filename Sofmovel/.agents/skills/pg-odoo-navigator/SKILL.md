---
name: pg-odoo-navigator
description: Navigate Parametro Global Odoo repositories with bounded context. Use for locating Odoo models, fields, Python classes, XML IDs, views, manifests, module dependencies, and Python-to-XML references before reading or changing source, especially in large Odoo repositories with a generated odools.toml.
---

# PG Odoo Navigator

## Workflow

1. Run the framework preflight required by `AGENTS.md`.
2. Verify OdooLS configuration without changing it:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .pg_framework\scripts\pg_setup_odools.ps1 -RepoPath (Get-Location).Path -CheckOnly
```

3. Prefer an already-running OdooLS instance in the IDE for interactive navigation. Do not start repeated cold OdooLS processes during one task.
4. For a deliberate one-off structural lookup, run a bounded query:

```powershell
python .pg_framework\scripts\pg_odools_query.py "<symbol-or-xmlid>" --repo . --limit 20 --timeout 600 --json
```

Cold indexing can take several minutes. If the result is not ready, use targeted `rg` patterns from [references/odoo-navigation.md](references/odoo-navigation.md); do not retry repeatedly.

5. Read only the returned files and the directly connected manifest/XML/Python definitions.
6. Before editing, open the complete target function or XML record and validate against the active Odoo version in `vendor/odoo_src`.

## Query terms

- Model: `sale.order` or the Python class name.
- XML ID: `xmlid.module.record_id`.
- Field: locate the model first, then search the bounded model/module paths.
- View/action/menu: query the XML ID or distinctive record suffix.
- Dependency: inspect the target module's `__manifest__.py`, then query referenced models or XML IDs.

## Guardrails

- Cap returned symbols at 20 unless the user requests a broader audit.
- Treat OdooLS locations as navigation hints, not proof; verify source before conclusions or edits.
- Never load all of `vendor/odoo_src` into context.
- Never query credentials, `.pg/migration`, customer exports, or generated documents.
- Fall back to targeted `rg` when OdooLS is unavailable or cold-start cost is disproportionate.
- Do not claim token savings without measured A/B results from comparable tasks.
