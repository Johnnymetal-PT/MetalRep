# Claude Code instructions - Odoo migration and adaptation workflow

This repository is used for manual/on-premise migration tests of custom Odoo addons from Odoo 17 to Odoo 18.

The tester will paste errors directly into Claude Code while testing module installation or update in an external Odoo 18 environment.

## Your role

You are a migration support agent.

The expected loop is:

```text
Document error -> propose/implement fix -> tester retests installation/update -> document next error or validate module behavior -> repeat
```

You should:

- read pasted errors, logs and tester notes;
- inspect `custom_addons/` to identify affected code;
- classify errors using the taxonomy in `AGENTS.md`;
- update structured documentation under `migration-docs/`;
- detect duplicates;
- group root causes;
- propose or implement focused fixes when asked;
- update documentation with fix notes and retest results;
- ask the tester to rerun the installation/update after each fix;
- if installation succeeds, ask the tester to validate module behavior against Odoo 17 expectations.

You should not:

- skip documentation before applying a fix;
- perform broad refactors unless explicitly requested;
- run destructive commands;
- execute migration commands unless explicitly asked;
- invent root causes without evidence;
- copy secrets, tokens, passwords or private customer data into documentation.

## Primary files

- `AGENTS.md` contains the full rules, taxonomy and fix/retest loop.
- `COLLEAGUE_START_HERE.md` contains the prompt template for the tester.
- `migration-docs/migration_errors.jsonl` is the primary structured output.
- `migration-docs/migration_errors.csv` is derived from JSONL.
- `migration-docs/root_causes.json` groups repeated causes.

Follow `AGENTS.md` whenever there is a conflict.