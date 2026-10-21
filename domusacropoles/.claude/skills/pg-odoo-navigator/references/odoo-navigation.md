# Odoo navigation patterns

Use these bounded fallbacks when OdooLS is unavailable or a cold start is not justified.

| Target | Command pattern |
|---|---|
| Model declaration/inheritance | `rg -n '(_name|_inherit)\s*=\s*["'']MODEL["'']' -g '*.py'` |
| Field declaration | `rg -n '^\s*FIELD\s*=\s*fields\.' -g '*.py'` |
| Python XML ID usage | `rg -n 'env\.ref\(["'']MODULE\.ID["'']\)' -g '*.py'` |
| XML record/reference | `rg -n '(id|ref|inherit_id)=["''](?:MODULE\.)?ID["'']' -g '*.xml'` |
| Module dependencies | Read only `MODULE/__manifest__.py` and the manifests of direct dependencies. |

Exclude `vendor/**`, `.pg/**`, `.pg_framework/**`, generated outputs, and credentials for project-only searches. Search `vendor/odoo_src` separately only when validating standard Odoo behavior.

After locating candidates, read the complete target function/record and its direct callers or inherited records. Do not treat a text match as semantic proof.
