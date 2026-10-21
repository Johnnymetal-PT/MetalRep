# AGENTS - Projeto com Framework Partilhado PG

## STOP - Ritual obrigatório antes de qualquer resposta
Correr sempre os `.ps1` com `powershell -NoProfile -ExecutionPolicy Bypass -File .pg_framework\scripts\<nome>.ps1` — num projeto os scripts estão em `.pg_framework\scripts\` (symlink para o `_pg_template`), não em `scripts\`; a *ExecutionPolicy* pode bloquear `.ps1` diretos (`PSSecurityException`).

Não prosseguir com análise, leitura funcional ou proposta sem executar e confirmar o **ritual único** definido em `.pg_framework/templates/AGENTS_SHARED.md` (secção "Ritual obrigatório no arranque de cada chat"). Em resumo, e por esta ordem:
- `1.` **checkout Brodoo** — `... -File .pg_framework\scripts\pg_checkout_brodoo_branch.ps1 -RepoPath <path_do_repo>`
- `2.` **framework atualizada** — `... -File .pg_framework\scripts\pg_ensure_framework_current.ps1 -RepoPath <path_do_repo>` (faz `git pull --ff-only` do `_pg_template` e re-sincroniza o projeto se houver drift; **não** usar `git pull` manual, que provoca divergência)
- `3.` **versão Odoo** confirmada antes de comandos dependentes de série
- `4.` **preflight** — `... -File .pg_framework\scripts\pg_preflight_context.ps1 -RepoPath <path_do_repo>` (validação abrangente de dependências → `.pg/PREFLIGHT.json`)

Se algum passo falhar, parar e reportar o bloqueio ao utilizador.
O passo 1 é pré-condição de todos os outros — sem a branch Brodoo correcta, os dados do contexto podem estar desactualizados ou pertencer ao branch de produção.

## Papel deste ficheiro
Este `AGENTS.md` é local ao projeto.
Serve para ligar o projeto ao framework partilhado e para registar overrides locais quando existirem.
É também a referência local comum importada por `CLAUDE.md`, para manter Claude e Codex alinhados sem duplicar regras.
O Antigravity lê este ficheiro nativamente, tal como o Codex. Não incluir o `AGENTS_SHARED.md` por `@[...](...)`: o Antigravity corta cada ficheiro de regras aos 24 KB, e o `AGENTS_SHARED.md` ficaria truncado sem aviso. Tem de ser lido integralmente com a ferramenta de leitura, como manda a secção seguinte.

## Framework partilhado obrigatório
Antes de concluir qualquer análise, recomendação ou proposta técnica, consultar obrigatoriamente:
1. `.pg_framework/templates/AGENTS_SHARED.md`
2. `PG_CONTEXT.md`
3. código do projeto
4. `vendor/odoo_src`
5. documentação oficial do Odoo da versão ativa registada no `PG_CONTEXT.md`

Para esta regra, `codigo do projeto` e `vendor/odoo_src` incluem também fontes locais relevantes expostas no repo atual por symlink, junction ou atalho estrutural equivalente.
O agente não se deve limitar a ficheiros versionados diretamente quando esses atalhos existirem.

Quando existirem, usar também:
- `PG_SCOPE_INTAKE.yaml`
- `.pg/PG_SCOPE_SYNC.json`
- `.pg/PG_EFFORT_SYNC.json`

Em modo multi-projeto (quando existir `.pg/PG_PROJECT_INDEX.json`), consultar também os artefactos por `project_key`:
- `.pg/projects/<project_key>/tasks/tasks.json`
- `.pg/projects/<project_key>/PG_SCOPE_SYNC.json`
- `.pg/projects/<project_key>/PG_EFFORT_SYNC.json`

Regra obrigatória em multi-projeto:
- usar primeiro os paths `.pg/projects/<project_key>/...` do projeto correto
- não usar `.pg/tasks/tasks.json` global como fonte principal quando existir estrutura namespaced
- se o `project_key` não estiver claro, parar e perguntar ao utilizador antes de continuar

Se `.pg_framework` não existir ou não estiver acessível, parar e pedir relink do framework partilhado antes de continuar.

## Arranque de chat (obrigatório)
No arranque de cada chat novo neste projeto, seguir o **ritual único** definido em `.pg_framework/templates/AGENTS_SHARED.md` (resumido na secção "STOP" acima). Não repetir aqui os passos, para evitar divergência entre ficheiros — a atualização da framework é feita por `pg_ensure_framework_current.ps1` (ff-only + re-sync), não por `git pull` manual.

## Overrides locais do projeto
- [Sem overrides locais neste momento]
