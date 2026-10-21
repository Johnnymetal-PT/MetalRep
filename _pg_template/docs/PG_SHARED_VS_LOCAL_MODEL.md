# PG_SHARED_VS_LOCAL_MODEL

Este documento clarifica o que deve ser partilhado entre projetos e o que deve permanecer local a cada repositório.

## Partilhado no framework

Permanecem no `_pg_template`:

- regras partilhadas do agente em `templates/AGENTS_SHARED.md`
- prompts e docs metodologicos em `docs/`
- scripts de bootstrap e automação em `scripts/`
- configuração base em `config.toml`
- patterns consultivos
- learnings reutilizáveis curados e desidentificados
- versionamento e changelog do framework

## Local a cada projeto

Permanecem no repositório do projeto:

- `AGENTS.md`
- `CLAUDE.md`
- `.pg_framework/`
- `PG_CONTEXT.md`
- `PG_SCOPE_INTAKE.yaml`
- `.pg/PG_SCOPE_SYNC.json`
- `vendor/odoo_src`
- código, configuração e histórico específico do projeto

## Regra simples

- o método e partilhado
- o contexto e local
- a aprendizagem transversal sobe ao framework apenas por curadoria explicita

## Implicação prática

`PG_CONTEXT.md` não deve ser usado como memória global de múltiplos projetos.
`PG_PROJECT_LEARNINGS.md` também não deve receber automaticamente texto bruto de projeto.
`AGENTS.md` no projeto passa a ser um wrapper leve, enquanto as regras partilhadas vivem em `.pg_framework/templates/AGENTS_SHARED.md`.
`CLAUDE.md` deve continuar a ser apenas o wrapper de compatibilidade do Claude Code, importando `AGENTS.md` e as regras partilhadas para manter paridade com Codex.
