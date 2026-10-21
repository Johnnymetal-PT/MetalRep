# PG-005 F1 Pilot Validation

## Objetivo

Validar em piloto que o suporte multi-projeto de F1 funciona sem regressão no modo legacy.

## Pré-requisitos

- Addon `pg_brodoo` atualizado para `19.0.1.1.0`.
- Migração `pg_brodoo/migrations/19.0.1.1.0/post-migrate.py` aplicada.
- Repo piloto com 2 projetos Odoo ligados ao mesmo repositório/branch.

## Cenário de teste

- Projeto A: com `pg_project_key` definido (ex.: `alpha-crm`).
- Projeto B: sem `pg_project_key` (legacy mode).

## Checklist funcional

- [ ] Projeto A publica scope para `.pg/projects/alpha-crm/PG_SCOPE_SYNC.json`.
- [ ] Projeto A publica context para `projects/alpha-crm/PG_CONTEXT.md`.
- [ ] Projeto A publica mirror artifacts em `.pg/projects/alpha-crm/...`.
- [ ] Projeto A atualiza `.pg/PG_PROJECT_INDEX.json` com `project_id` e `project_key`.
- [ ] Projeto B continua a publicar scope para `.pg/PG_SCOPE_SYNC.json`.
- [ ] Projeto B continua a publicar context para `PG_CONTEXT.md`.
- [ ] Projeto B não sofre alteração de comportamento vs legado.

## Checklist de robustez

- [ ] Falha ao atualizar `PG_PROJECT_INDEX.json` não bloqueia sync principal.
- [ ] `snapshot_path` dos runs reflete path namespaced quando há `pg_project_key`.
- [ ] `snapshot_path` dos runs mantém path legacy sem `pg_project_key`.
- [ ] `pg_project_key` inválido falha com mensagem de validação.
- [ ] Colisão de `pg_project_key` no mesmo `repo+branch` falha com validação.

## Evidência mínima

- [ ] Links/commits dos ficheiros publicados para Projeto A e Projeto B.
- [ ] Captura/listagem de runs (`pg.project.*.sync.run`) com `snapshot_path`.
- [ ] Exemplo do conteúdo de `.pg/PG_PROJECT_INDEX.json`.
- [ ] Nota curta de resultado final: `PASS` ou `FAIL` com motivo.

## Critério de conclusão F1

F1 só é considerado concluído quando todos os itens desta checklist estiverem marcados e com evidência registada.
