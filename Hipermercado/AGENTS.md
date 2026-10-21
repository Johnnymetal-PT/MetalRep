# AGENTS - Projeto com Framework Partilhado PG

## STOP - Ritual obrigatório antes de qualquer resposta
Não prosseguir com análise, leitura funcional ou proposta sem executar e confirmar:
- `1.` `scripts/pg_checkout_brodoo_branch.ps1 -RepoPath <path_do_repo>` — garante checkout e pull na branch Brodoo antes de qualquer outra acção
- `2.` `git pull` no repositório `_pg_template`
- `3.` verificar se o commit atual do `_pg_template` é diferente de `.pg/PG_TEMPLATE_SYNC_STATE.json -> template_git_head`
- `4.` bootstrap apenas se houver diferença, se não existir estado de sync, ou se o utilizador pedir
- `5.` confirmação da versão Odoo antes de comandos que dependem de série; se não houver informação fiável no repo, pedir ao utilizador antes de continuar

Se algum passo falhar, parar e reportar o bloqueio ao utilizador.
O passo 1 é pré-condição de todos os outros — sem a branch Brodoo correcta, os dados do contexto podem estar desactualizados ou pertencer ao branch de produção.

## Papel deste ficheiro
Este `AGENTS.md` é local ao projeto.
Serve para ligar o projeto ao framework partilhado e para registar overrides locais quando existirem.
É também a referência local comum importada por `CLAUDE.md`, para manter Claude e Codex alinhados sem duplicar regras.

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
- `.pg/PG_PROJECT_STATUS_SYNC.json`
- `.pg/PG_EFFORT_SYNC.json`

Em modo multi-projeto (quando existir `.pg/PG_PROJECT_INDEX.json`), consultar também os artefactos por `project_key`:
- `.pg/projects/<project_key>/tasks/tasks.json`
- `.pg/projects/<project_key>/PG_SCOPE_SYNC.json`
- `.pg/projects/<project_key>/PG_PROJECT_STATUS_SYNC.json`
- `.pg/projects/<project_key>/PG_EFFORT_SYNC.json`

Regra obrigatória em multi-projeto:
- usar primeiro os paths `.pg/projects/<project_key>/...` do projeto correto
- não usar `.pg/tasks/tasks.json` global como fonte principal quando existir estrutura namespaced
- se o `project_key` não estiver claro, parar e perguntar ao utilizador antes de continuar

Se `.pg_framework` não existir ou não estiver acessível, parar e pedir relink do framework partilhado antes de continuar.

## Arranque de chat (obrigatório)
No arranque de cada chat novo neste projeto, seguir o ritual definido em `.pg_framework/templates/AGENTS_SHARED.md`:
- `git pull` no `_pg_template`
- `git pull` no repositório do projeto atual
- bootstrap condicional (só quando o `_pg_template` mudou desde o último sync registado)
- confirmar versão Odoo antes de comandos que dependem da série; se a versão não estiver clara, pedir ao utilizador antes de correr o comando

## Overrides locais do projeto
- [Sem overrides locais neste momento]
