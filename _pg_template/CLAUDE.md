# CLAUDE - _pg_template

Este ficheiro existe para Claude Code quando a sessão abre diretamente no repositório `_pg_template`.

As regras partilhadas que os projetos recebem vivem em:
@templates/AGENTS_SHARED.md

Os wrappers copiados para cada projeto vivem em:
@templates/AGENTS.md
@templates/CLAUDE.md

## Regra de compatibilidade
Qualquer alteração feita para Codex em `templates/AGENTS.md` deve manter comportamento equivalente para Claude em `templates/CLAUDE.md`.
Evitar duplicar regras entre ficheiros; preferir imports/wrappers para reduzir divergência.

