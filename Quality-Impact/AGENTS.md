# AGENTS - Projeto com Framework Partilhado PG

## STOP - Ritual obrigatorio antes de qualquer resposta
Nao prosseguir com analise, leitura funcional ou proposta sem executar e confirmar:
- `1.` `git pull` no repositorio `_pg_template`
- `2.` `git pull` no repositorio do projeto atual
- `3.` verificar se o commit atual do `_pg_template` e diferente de `.pg/PG_TEMPLATE_SYNC_STATE.json -> template_git_head`
- `4.` bootstrap apenas se houver diferenca, se nao existir estado de sync, ou se o utilizador pedir
- `5.` confirmacao da versao Odoo antes de comandos que dependem de serie; se nao houver informacao fiavel no repo, pedir ao utilizador antes de continuar

Se algum passo falhar, parar e reportar o bloqueio ao utilizador.

## Papel deste ficheiro
Este `AGENTS.md` e local ao projeto.
Serve para ligar o projeto ao framework partilhado e para registar overrides locais quando existirem.
E tambem a referencia local comum importada por `CLAUDE.md`, para manter Claude e Codex alinhados sem duplicar regras.

## Framework partilhado obrigatorio
Antes de concluir qualquer analise, recomendacao ou proposta tecnica, consultar obrigatoriamente:
1. `.pg_framework/templates/AGENTS_SHARED.md`
2. `PG_CONTEXT.md`
3. codigo do projeto
4. `vendor/odoo_src`
5. documentacao oficial do Odoo da versao ativa registada no `PG_CONTEXT.md`

Para esta regra, `codigo do projeto` e `vendor/odoo_src` incluem tambem fontes locais relevantes expostas no repo atual por symlink, junction ou atalho estrutural equivalente.
O agente nao se deve limitar a ficheiros versionados diretamente quando esses atalhos existirem.

Quando existirem, usar tambem:
- `PG_SCOPE_INTAKE.yaml`
- `.pg/PG_SCOPE_SYNC.json`
- `.pg/PG_PROJECT_STATUS_SYNC.json`
- `.pg/PG_EFFORT_SYNC.json`

Em modo multi-projeto (quando existir `.pg/PG_PROJECT_INDEX.json`), consultar tambem os artefactos por `project_key`:
- `.pg/projects/<project_key>/tasks/tasks.json`
- `.pg/projects/<project_key>/PG_SCOPE_SYNC.json`
- `.pg/projects/<project_key>/PG_PROJECT_STATUS_SYNC.json`
- `.pg/projects/<project_key>/PG_EFFORT_SYNC.json`

Regra obrigatoria em multi-projeto:
- usar primeiro os paths `.pg/projects/<project_key>/...` do projeto correto
- nao usar `.pg/tasks/tasks.json` global como fonte principal quando existir estrutura namespaced
- se o `project_key` nao estiver claro, parar e perguntar ao utilizador antes de continuar

Se `.pg_framework` nao existir ou nao estiver acessivel, parar e pedir relink do framework partilhado antes de continuar.

## Arranque de chat (obrigatorio)
No arranque de cada chat novo neste projeto, seguir o ritual definido em `.pg_framework/templates/AGENTS_SHARED.md`:
- `git pull` no `_pg_template`
- `git pull` no repositorio do projeto atual
- bootstrap condicional (so quando o `_pg_template` mudou desde o ultimo sync registado)
- confirmar versao Odoo antes de comandos que dependem da serie; se a versao nao estiver clara, pedir ao utilizador antes de correr o comando

## Overrides locais do projeto
- [Sem overrides locais neste momento]
