# Migration docs

Esta pasta contém a documentação estruturada gerada por Codex/Claude com base nos erros colados pelo colega durante os testes Odoo 17 -> 18.

## Fonte principal

- `migration_errors.jsonl` é a fonte principal estruturada.
- `migration_errors.csv` é uma cópia tabular para Excel/Sheets.
- `root_causes.json` agrupa erros com a mesma causa raiz.
- `errors/MIG-XXXX.md` contém fichas detalhadas para erros relevantes.
- `summaries/` contém resumos por ciclo de teste.

## Regra

Não editar manualmente `migration_errors.jsonl` salvo necessidade. Preferir pedir ao Codex/Claude para atualizar a documentação seguindo `AGENTS.md`.
