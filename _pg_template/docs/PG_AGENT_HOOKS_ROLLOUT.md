# Rollout e validação end-to-end dos hooks de registo de tokens (AUD-03)

Este checklist serve para **provar em runtime real**, num projeto-piloto, toda a cadeia construída (preflight, M1/M3, consumo de artefactos, registo automático de tokens) **antes** de propagar aos restantes projetos. A lição do incidente AUD-04: o que passa offline pode partir em runtime — por isso valida-se num repo antes de 65.

> Notas: os hooks só existem em projetos **novos** (bootstrap) ou após propagação (abaixo). Os números de tokens do Claude são **aproximados** (`estimated`); os do Codex são **reais** (`measured`, via rollout); os do Antigravity são **aproximados** (`estimated`, via transcript da conversa). Custo autoritário = Consoles Anthropic/OpenAI.

## Fase 0 — Propagar ao projeto-piloto

Escolher um projeto de baixo risco. Pré-visualizar e depois aplicar:

```powershell
# pré-visualizar (não escreve)
.\scripts\pg_propagate_agent_hooks.ps1 -RepoPath "C:\Users\<u>\Desktop\Repos\<PILOTO>" -WhatIf
# aplicar
.\scripts\pg_propagate_agent_hooks.ps1 -RepoPath "C:\Users\<u>\Desktop\Repos\<PILOTO>"
```

Confirmar que o repo passou a ter `.claude/settings.json`, `.codex/hooks.json`, `.agents/hooks.json` e `.pg/tokens/consumption.jsonl`.

## Fase 1 — Validar Claude Code (sessão real no piloto)

1. Abrir uma sessão de Claude Code no repo-piloto. Na 1.ª vez, **autorizar o workspace (trust)** para os hooks correrem.
2. Ritual de arranque: confirmar que o **preflight** corre e escreve `.pg/PREFLIGHT.json` com `status`, `odoo_series`, `docs_base_url`, `source_ok`.
3. Pedir ao agente uma análise que exija a **ordem standard-vs-custom** e confirmar que ele **consulta `odoo_env.json`** (módulos instalados) e, se aplicável, `deliverables.json` e a metodologia (`doc_templates`).
4. Fechar a sessão. Confirmar que o `.pg/tokens/consumption.jsonl` ganhou um `session_open` e um `session_close` (agent `claude`, `token_measurement:"estimated"`, `read_mode` preenchido).

## Fase 2 — Validar Codex (sessão real no piloto)

1. Confirmar a **feature experimental de hooks** ativa (`[features] hooks = true` no `config.toml`) e a versão do `codex` (~v0.114.0+). `PONTO POR VALIDAR`: hooks project-local podem não disparar em sessões interativas em versões com bug.
2. Abrir uma sessão de Codex no repo-piloto e trabalhar um ou dois turnos.
3. Confirmar no `.pg/tokens/consumption.jsonl`: `session_open` (codex) e **um** `session_close` (codex) com `token_measurement:"measured"` e tokens reais (do rollout). Repetir um turno e confirmar que **não duplica** (upsert).

## Fase 2b — Validar Antigravity (sessão real no piloto)

O Antigravity tem outro contrato de hooks: não há `SessionStart` nem `SessionEnd`, o payload vem em camelCase, o hook corre a partir de `.agents/` e o stdout tem de ser JSON. O `pg_hook_antigravity.ps1` reconstrói o arranque na **primeira** `PreInvocation` de cada conversa. Fonte do contrato: a documentação que a própria extensão instala em `~/.gemini/antigravity/builtin/skills/agy-customizations/docs/hooks.md`.

1. Abrir uma conversa do Antigravity no repo-piloto e enviar uma mensagem.
2. Confirmar que o agente recebeu a mensagem `PG FRAMEWORK (hook Antigravity...)` e que leu o `AGENTS_SHARED.md` **por inteiro** antes de responder. O Antigravity corta cada ficheiro de regras aos 24 KB, e o `AGENTS_SHARED.md` tem mais do dobro: se o agente responder citando só o início, o contrato não chegou.
3. Confirmar no `.pg/tokens/consumption.jsonl`: um `session_open` (agent `antigravity`, `session_id` = `conversationId`) e, após dois turnos, **um** `session_close`.
4. Confirmar que o `session_close` traz tokens (`token_accounting:"unique_input_v2"`) e `read_mode:"mirror"` numa sessão que não tocou na API do Odoo. `FACTO OBSERVADO` (enigmaf, 2026-10-07, conversa `03be5fff`): o hook disparou, o agente leu o `AGENTS_SHARED.md`, correu os passos 1, 2 e 4 do ritual e respondeu com o aviso do inventário; o transcript fica em `~/.gemini/antigravity/brain/<conversationId>/.system_generated/logs/transcript.jsonl`, com um `PLANNER_RESPONSE` por chamada ao modelo.
5. Auto-bootstrap: com `py scripts\pg_install_user_hooks.py` corrido numa máquina com Antigravity, o hook de utilizador (`~/.gemini/config/hooks.json`) corre na primeira invocação de cada conversa. `FACTO OBSERVADO` (2026-10-08): validado com a linha de comandos do Antigravity, que usa o mesmo motor de hooks da extensão. Numa pasta git vazia, `agy -p "<pedido>" --log-file <ficheiro>` registou `loaded 1 named hooks from 1 hooks.json file(s)` e nenhuma falha. Para repetir a verificação noutra máquina, procurar no log `hooks_manager` e `failed to call custom pre-invocation hook`. Na versão 2.44.0 o comando levava o caminho entre aspas duplas e falhava sempre (`Caracteres inválidos no caminho`); corrigido na v2.44.2.

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
- Hooks Claude, Codex e Antigravity escrevem consumo automaticamente (open+close), sem duplicar.
- Relatório agrega e distingue mirror vs api.
