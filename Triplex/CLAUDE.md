# CLAUDE - Projeto com Framework Partilhado PG

## Ação obrigatória antes de qualquer resposta
Correr sempre os `.ps1` com `powershell -NoProfile -ExecutionPolicy Bypass -File .pg_framework\scripts\<nome>.ps1` — num projeto os scripts estão em `.pg_framework\scripts\` (symlink para o `_pg_template`), não em `scripts\`; a *ExecutionPolicy* pode bloquear `.ps1` diretos (`PSSecurityException`).

Antes de ler contexto funcional ou responder ao utilizador, executar o **ritual único** definido em `.pg_framework/templates/AGENTS_SHARED.md` (secção "Ritual obrigatório no arranque de cada chat"). Em resumo, e por esta ordem:
1. **checkout Brodoo** — `... -File .pg_framework\scripts\pg_checkout_brodoo_branch.ps1 -RepoPath <path_do_repo_atual>`
2. **framework atualizada** — `... -File .pg_framework\scripts\pg_ensure_framework_current.ps1 -RepoPath <path_do_repo_atual>` (faz `git pull --ff-only` do `_pg_template` e re-sincroniza o projeto se houver drift; **não** usar `git pull` manual, que provoca divergência)
3. **versão Odoo** confirmada antes de comandos dependentes de série
4. **preflight** — `... -File .pg_framework\scripts\pg_preflight_context.ps1 -RepoPath <path_do_repo_atual>` (validação abrangente → `.pg/PREFLIGHT.json`)

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
