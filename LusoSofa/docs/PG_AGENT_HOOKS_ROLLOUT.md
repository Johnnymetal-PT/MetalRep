# Rollout e validação end-to-end dos hooks de registo de tokens (AUD-03)

Este checklist serve para **provar em runtime real**, num projeto-piloto, toda a cadeia construída (preflight, M1/M3, consumo de artefactos, registo automático de tokens) **antes** de propagar aos restantes projetos. A lição do incidente AUD-04: o que passa offline pode partir em runtime — por isso valida-se num repo antes de 65.

> Notas: os hooks só existem em projetos **novos** (bootstrap) ou após propagação (abaixo). Os números de tokens do Claude são **aproximados** (`estimated`); os do Codex são **reais** (`measured`, via rollout). Custo autoritário = Consoles Anthropic/OpenAI.

## Fase 0 — Propagar ao projeto-piloto

Escolher um projeto de baixo risco. Pré-visualizar e depois aplicar:

```powershell
# pré-visualizar (não escreve)
.\scripts\pg_propagate_agent_hooks.ps1 -RepoPath "C:\Users\<u>\Desktop\Repos\<PILOTO>" -WhatIf
# aplicar
.\scripts\pg_propagate_agent_hooks.ps1 -RepoPath "C:\Users\<u>\Desktop\Repos\<PILOTO>"
```

Confirmar que o repo passou a ter `.claude/settings.json`, `.codex/hooks.json` e `.pg/tokens/consumption.jsonl`.

## Fase 1 — Validar Claude Code (sessão real no piloto)

1. Abrir uma sessão de Claude Code no repo-piloto. Na 1.ª vez, **autorizar o workspace (trust)** para os hooks correrem.
2. Ritual de arranque: confirmar que o **preflight** corre e escreve `.pg/PREFLIGHT.json` com `status`, `odoo_series`, `docs_base_url`, `source_ok`.
3. Pedir ao agente uma análise que exija a **ordem standard-vs-custom** e confirmar que ele **consulta `odoo_env.json`** (módulos instalados) e, se aplicável, `deliverables.json` e a metodologia (`doc_templates`).
4. Fechar a sessão. Confirmar que o `.pg/tokens/consumption.jsonl` ganhou um `session_open` e um `session_close` (agent `claude`, `token_measurement:"estimated"`, `read_mode` preenchido).

## Fase 2 — Validar Codex (sessão real no piloto)

1. Confirmar a **feature experimental de hooks** ativa (`[features] hooks = true` no `config.toml`) e a versão do `codex` (~v0.114.0+). `PONTO POR VALIDAR`: hooks project-local podem não disparar em sessões interativas em versões com bug.
2. Abrir uma sessão de Codex no repo-piloto e trabalhar um ou dois turnos.
3. Confirmar no `.pg/tokens/consumption.jsonl`: `session_open` (codex) e **um** `session_close` (codex) com `token_measurement:"measured"` e tokens reais (do rollout). Repetir um turno e confirmar que **não duplica** (upsert).

## Fase 3 — Relatório agregado

```powershell
.\scripts\pg_report_token_consumption.ps1 -RepoPath "C:\Users\<u>\Desktop\Repos\<PILOTO>"
```

Confirmar totais e a repartição por `read_mode` (mirror vs api).

## Fase 4 — Propagar a todos (só depois do piloto validar)

```powershell
# pré-visualizar em todos os repos sob a pasta
.\scripts\pg_propagate_agent_hooks.ps1 -RootPath "C:\Users\<u>\Desktop\Repos" -WhatIf
# aplicar
.\scripts\pg_propagate_agent_hooks.ps1 -RootPath "C:\Users\<u>\Desktop\Repos"
```

Por defeito **não sobrescreve** ficheiros já existentes (usar `-Force` para atualizar quando o hook evoluir). Rever periodicamente o agregado (`-RootPath`) para tendência de custo por projeto; o controlo de orçamento é nos Consoles.

## Critérios de aceitação
- Preflight escreve `PREFLIGHT.json` e bloqueia quando faltam fontes.
- Agente consulta `odoo_env.json`/`deliverables.json`/metodologia na decisão.
- Hooks Claude e Codex escrevem consumo automaticamente (open+close), sem duplicar.
- Relatório agrega e distingue mirror vs api.
