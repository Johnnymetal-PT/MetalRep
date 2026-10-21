# CLAUDE - Projeto com Framework Partilhado PG

## Acao obrigatoria antes de qualquer resposta
Antes de ler contexto funcional ou responder ao utilizador, executar:
1. `git -C <path_do__pg_template> pull`
2. `git -C <path_do_repo_atual> pull`
3. comparar `git -C <path_do__pg_template> rev-parse HEAD` com `.pg/PG_TEMPLATE_SYNC_STATE.json -> template_git_head` no repo atual
4. executar bootstrap apenas se houver diferenca, se nao existir estado de sync, ou se o utilizador pedir
5. validar versao Odoo do repo antes de comandos dependentes de serie; se faltar, pedir ao utilizador

Se nao for possivel localizar `_pg_template` ou executar os comandos, parar e pedir os dados em falta.

Este ficheiro existe para Claude Code.
Nao duplicar regras aqui: o contrato local comum continua em `AGENTS.md`, para que Claude e Codex sigam as mesmas instrucoes.

@AGENTS.md
@.pg_framework/templates/AGENTS_SHARED.md

## Regra de compatibilidade
Se algum import acima falhar, parar antes de concluir analise, recomendacao ou implementacao e pedir relink/bootstrap do framework partilhado.

Claude deve seguir o mesmo contrato de descoberta do `AGENTS.md`:
- considerar ficheiros do repo atual
- considerar tambem fontes locais relevantes expostas por symlink, junction ou atalho estrutural equivalente
- nao tratar a ausencia de leitura dessas fontes como se a validacao estivesse completa
