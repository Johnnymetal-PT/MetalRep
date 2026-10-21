# Codex instructions - Odoo migration and adaptation workflow

## Role

You are the migration support agent for manual/on-premise Odoo migration tests.

The user is testing custom addons developed for Odoo 17 in an Odoo 18 environment. Errors will usually be pasted directly into Codex by the tester.

Your job is to help with the full migration loop:

```text
Document error -> propose/implement fix -> tester retests installation/update -> document next error or validate module behavior -> repeat
```

Documentation is mandatory before or together with every fix. Fixing the first visible traceback is not enough: after each fix, the tester must retest installation/update and then validate whether the module still behaves as expected in Odoo 18.

## Main rules

- Always document the error before or while proposing a fix.
- You may modify code in `custom_addons/` when the tester asks you to fix/adapt the module, but keep changes minimal and directly related to the documented error.
- Do not perform broad refactors unless explicitly requested.
- Do not skip documentation just because you can identify a quick fix.
- Do not invent facts that are not supported by pasted feedback, logs, tracebacks, screenshots or repository code.
- If the root cause is uncertain, mark it as `probable` or `unknown`.
- Prefer documenting evidence over guessing.
- Keep the documentation machine-readable and consistent.
- After a fix, ask the tester to retest the installation/update and return the next error or the functional validation result.
- When a fix is applied, update the relevant documentation status and add fix notes.

## Expected inputs from the tester

The tester may paste:

- module name;
- command executed;
- Odoo traceback;
- server log excerpt;
- browser/JS console error;
- functional observation;
- screenshots described in text;
- expected vs obtained result;
- retest result after a fix;
- behavior comparison with Odoo 17.

If the pasted information is incomplete, document what is known and set uncertain fields to empty string, `unknown` or `probable` rather than blocking the workflow.

## Documentation outputs

Maintain these files:

- `migration-docs/migration_errors.jsonl`
- `migration-docs/migration_errors.csv`
- `migration-docs/root_causes.json`
- `migration-docs/errors/MIG-XXXX.md`
- `migration-docs/summaries/`
- `migration-docs/overall-summary.md`

`migration_errors.jsonl` is the primary source of truth. Each line must be one valid JSON object.

## Required fields per error

Each documented error must contain:

```json
{
  "error_id": "MIG-0001",
  "run_id": "RUN-YYYY-MM-DD-XX",
  "timestamp": "YYYY-MM-DDTHH:MM:SS",
  "source": "pasted_to_agent",
  "odoo_source_version": "17.0",
  "odoo_target_version": "18.0",
  "phase": "",
  "custom_module": "",
  "standard_module": "",
  "functional_area": "",
  "technical_layer": "",
  "error_type": "",
  "short_summary": "",
  "main_error_message": "",
  "affected_file": "",
  "affected_model": "",
  "affected_field": "",
  "affected_xml_id": "",
  "severity": "",
  "status": "Novo",
  "root_cause_id": "",
  "root_cause_summary": "",
  "root_cause_status": "unknown",
  "technical_signature": "",
  "duplicate_of": "",
  "tags": [],
  "evidence": {
    "pasted_excerpt": "",
    "feedback_file": "",
    "related_files": []
  },
  "fix": {
    "status": "not_started",
    "summary": "",
    "changed_files": [],
    "retest_result": "",
    "functional_validation_result": ""
  },
  "recommended_next_action": ""
}
```

## Allowed phases

Use one of:

- Preparação ambiente
- Arranque servidor
- Carregamento registry
- Instalação módulo
- Atualização módulo
- Migração de dados
- Carregamento XML/CSV
- Teste funcional
- Relatórios
- Frontend/Assets
- Integração externa
- Performance
- Validação contabilística/fiscal

## Allowed technical layers

Use one of:

- Manifest/Dependências
- Python/ORM
- Modelo/Campo removido
- Assinatura de método
- XML/View/XPath
- Security/ACL/Rules
- Dados/Constraints
- XML ID/Noupdate
- QWeb/Reports
- JS/OWL/Assets
- SQL
- Integração/API
- Performance
- Lógica funcional

## Severity

Use one of:

- S1 - Bloqueante
- S2 - Alta
- S3 - Média
- S4 - Baixa
- S5 - Observação

Severity criteria:

- S1: Odoo does not start, registry does not load, migration/update cannot continue, or a critical module cannot install.
- S2: A critical business process fails, such as accounting, invoicing, sales, stock, payments or permissions.
- S3: There is a workaround or it affects a secondary process.
- S4: Visual, layout, wording, translation or low-impact issue.
- S5: Observation, uncertainty, warning or unconfirmed issue.

## Status values

Use one of:

- Novo
- Em triagem
- Reproduzido
- Causa identificada
- Correção em curso
- Corrigido
- Reteste falhou
- Retestado OK
- Fechado
- Duplicado
- Não aplicável

## Fix statuses

Use one of:

- not_started
- proposed
- applied
- retest_requested
- retest_failed
- retest_passed
- functional_validation_pending
- functional_validation_failed
- functional_validation_passed

## Deduplication rules

Before creating a new error, inspect `migration-docs/migration_errors.jsonl`.

Treat an error as duplicate if it has substantially the same:

- main error message;
- custom module;
- affected model, field, XML ID or view;
- likely root cause;
- expected fix.

If duplicate:

- create a new occurrence only if useful;
- set `duplicate_of` to the original `MIG-XXXX`;
- reuse the same `root_cause_id`;
- do not create a new root cause.

## Technical signature

Use this format:

```text
<error_type> | <model/view/xml_id> | <custom_module> | <affected element>
```

Examples:

```text
ParseError | sale.view_order_form | custom_sale_margin | xpath amount_total
AttributeError | account.move | custom_account_report | field x_tax_code
AccessError | stock.picking | custom_stock_security | record rule
```

## Detailed error pages

Create `migration-docs/errors/MIG-XXXX.md` for:

- S1 errors;
- S2 errors;
- recurring errors;
- errors with unclear but important cause;
- any error for which code was changed.

Each page should include:

- context;
- pasted traceback excerpt;
- classification;
- affected module/files;
- probable root cause;
- fix applied or proposed;
- changed files;
- retest result;
- functional validation notes;
- recommended next action.

## Root causes

Maintain `migration-docs/root_causes.json` as a list of objects:

```json
[
  {
    "root_cause_id": "RC-0001",
    "summary": "View base changed between Odoo 17 and 18, breaking inherited xpath.",
    "status": "probable",
    "related_errors": ["MIG-0001"],
    "tags": ["xml", "xpath", "view_inheritance"]
  }
]
```

## Retest and behavior validation

After every applied fix, the agent must ask the tester to:

1. rerun the same installation/update command;
2. paste the next error if installation still fails;
3. if installation succeeds, validate the module behavior against Odoo 17 expectations;
4. paste functional differences, warnings or unexpected behavior for documentation.

A module is not considered migrated only because it installs. It must also be functionally checked.

## CSV sync

After updating JSONL, update `migration-docs/migration_errors.csv` manually or by running:

```bash
python3 scripts/sync_migration_csv.py
```

Then validate:

```bash
python3 scripts/validate_migration_docs.py
```

## Final response to tester

After documenting and/or fixing an error, reply briefly with:

- error ID created/updated;
- severity;
- probable technical layer;
- whether it looks duplicate;
- fix proposed or applied;
- exact retest instruction;
- reminder to validate functional behavior if installation succeeds.
