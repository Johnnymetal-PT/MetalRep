# PG-005 F1 — Handoff para Codex

## O que é este bundle

Instruções de implementação para a fase F1 do item PG-005 do backlog da framework.

**Objectivo**: adicionar suporte a múltiplos projetos Odoo no mesmo repositório GitHub e branch, sem quebrar projetos existentes (modo legacy).

**Scope**: apenas o addon `pg_brodoo`. Os scripts PowerShell do `_pg_template` são tratados em paralelo ou a seguir (scope do F1 no lado do template).

## Como usar com Codex

### Opção A — AGENTS.md override (recomendado)

1. Copiar `AGENTS.md` deste bundle para a raiz do repo onde `pg_brodoo` vive.
2. Abrir Codex nesse repo.
3. Codex lê `AGENTS.md` automaticamente no início de cada sessão.
4. Executar a tarefa seguindo a sequência de implementação descrita.
5. Quando F1 estiver concluído: remover o `AGENTS.md` temporário e restaurar o original.

### Opção B — Prompt directo

Copiar o conteúdo de `AGENTS.md` como prompt inicial para Codex. Funciona se o repo não tiver `AGENTS.md` próprio ou se quiser usar Codex num repo separado.

## O que Codex deve implementar

Ver `AGENTS.md` para a spec completa. Resumo:

1. Campo `pg_project_key` em `project.project`
2. Refactor de `github_repository_publisher.py` (paths dinâmicos)
3. Padrão `_build_publisher(project)` em 9 serviços de sync
4. `update_project_index` chamado após publish bem-sucedido
5. View: campo visível no formulário do projeto
6. Bump de versão + migração
7. Testes unitários

## Critérios de aceitação

Todos os testes novos a passar + testes existentes sem regressão + projetos sem `pg_project_key` funcionam exactamente como antes.

## Referências no `_pg_template`

- `docs/PG_005_ARCHITECTURE_CONTRACT.md` — contrato arquitetural
- `docs/PG_005_BRODOO_CHANGE_SPEC.md` — spec detalhada
- `docs/PG_FRAMEWORK_IMPROVEMENT_BACKLOG.md` — contexto backlog

## O que fica para F2 (não implementar agora)

- Índice global `PG_CONTEXT.md` na raiz em modo multi-projeto
- Wizard de onboarding multi-projeto
- Migração de artefactos legacy existentes no GitHub
- Scripts PowerShell do `_pg_template` com `-ProjectKey`
