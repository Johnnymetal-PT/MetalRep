# CLAUDE - Projeto com Framework Partilhado PG

## Ação obrigatória antes de qualquer resposta
Antes de ler contexto funcional ou responder ao utilizador, executar:
1. `& "<path_do__pg_template>/scripts/pg_checkout_brodoo_branch.ps1" -RepoPath "<path_do_repo_atual>"` — garante que o repo está na branch Brodoo correcta antes de qualquer leitura
2. `git -C <path_do__pg_template> pull`
3. comparar `git -C <path_do__pg_template> rev-parse HEAD` com `.pg/PG_TEMPLATE_SYNC_STATE.json -> template_git_head` no repo atual
4. executar bootstrap apenas se houver diferença, se não existir estado de sync, ou se o utilizador pedir
5. validar versão Odoo do repo antes de comandos dependentes de série; se faltar, pedir ao utilizador

Se não for possível localizar `_pg_template` ou executar os comandos, parar e pedir os dados em falta.
O passo 1 é pré-condição de todos os outros — leituras feitas antes do checkout podem reflectir o branch de produção e não os dados do Brodoo.

Este ficheiro existe para Claude Code.
Não duplicar regras aqui: o contrato local comum continua em `AGENTS.md`, para que Claude e Codex sigam as mesmas instruções.

@AGENTS.md
@.pg_framework/templates/AGENTS_SHARED.md

## Regra de compatibilidade
Se algum import acima falhar, parar antes de concluir análise, recomendação ou implementação e pedir relink/bootstrap do framework partilhado.

Claude deve seguir o mesmo contrato de descoberta do `AGENTS.md`:
- considerar ficheiros do repo atual
- considerar também fontes locais relevantes expostas por symlink, junction ou atalho estrutural equivalente
- não tratar a ausência de leitura dessas fontes como se a validação estivesse completa
