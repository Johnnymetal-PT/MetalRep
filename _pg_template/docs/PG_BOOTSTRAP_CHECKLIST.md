# PG - Checklist rapido de bootstrap

## Pre-requisitos

- Repositórios em `C:\Users\Utilizador\Desktop\Repos`
- Template `_pg_template` disponível
- Git disponível no PATH
- acesso ao GitHub oficial do Odoo para clonar `odoo/odoo`
- acesso ao repositrio `odoo/enterprise`, quando o projeto for Enterprise

## Passos

1. Fluxo curto recomendado:

```powershell
cd C:\Users\Utilizador\Desktop\Repos\_pg_template
.\scripts\pg_bootstrap_assisted.ps1 -RepoName "NOME_DO_REPO" -CloneOdooSource -Series 19.0 -Edition community
```

2. Em alternativa, fluxo faseado:

```powershell
cd C:\Users\Utilizador\Desktop\Repos\_pg_template
.\scripts\pg_bootstrap_repo.ps1 -RepoName "NOME_DO_REPO"
```

3. Fazer checkout do source Odoo:

```cmd
cd /d C:\Users\Utilizador\Desktop\Repos\_pg_template
.\scripts\pg_clone_odoo_source.cmd NOME_DO_REPO [19.0|19e] [community|enterprise]
```

4. Confirmar no repositório bootstrapado:
- `AGENTS.md`
- `CLAUDE.md`
- `.pg_framework/`
- `.github/workflows/pg_refresh_pg_context.yml`
- `PG_CONTEXT.md`
- `PG_SCOPE_INTAKE.yaml`
- `config.toml`
- `.pg/PG_SCOPE_SYNC.json`
- `vendor/odoo_src/community`
- `vendor/odoo_src/enterprise` quando aplicável

5. Inicializar ou rever `PG_SCOPE_INTAKE.yaml`.

6. Materializar o contexto inicial:

```powershell
.\scripts\pg_build_pg_context.ps1 -RepoPath "C:\Users\Utilizador\Desktop\Repos\NOME_DO_REPO"
```

7. Validar e complementar no `PG_CONTEXT.md`:
- edição
- ambiente
- restrições contratuais
- pedido funcional atual
- processo atual
- dor / impacto

8. Quando existir scope sync vindo do Odoo:

```powershell
.\scripts\pg_validate_scope_sync.ps1 -RepoPath "C:\Users\Utilizador\Desktop\Repos\NOME_DO_REPO"
.\scripts\pg_apply_scope_sync.ps1 -RepoPath "C:\Users\Utilizador\Desktop\Repos\NOME_DO_REPO"
```

9. Validar rapidamente o repositório bootstrapado:

```powershell
.\scripts\pg_smoke_test_repo.ps1 -RepoPath "C:\Users\Utilizador\Desktop\Repos\NOME_DO_REPO" -RequireOdooSource
```

Se o projeto também versionar o addon:

```powershell
.\scripts\pg_smoke_test_repo.ps1 -RepoPath "C:\Users\Utilizador\Desktop\Repos\NOME_DO_REPO" -RequireOdooSource -CheckPgAiDevAssistant
```

10. Quando o `_pg_template` evoluir e for preciso alinhar um repositório já bootstrapado:

```powershell
.\scripts\pg_sync_shared_assets.ps1 -RepoName "NOME_DO_REPO"
```

O sync passa também a atualizar `.pg/PG_TEMPLATE_SYNC_STATE.json`, para deixar rasto do último alinhamento com os assets partilhados do framework.

Neste modelo, a propagação fica dividida em dois canais:
- ficheiros copiados para a raiz do projeto, como `AGENTS.md`, `CLAUDE.md`, `config.toml` e workflow GitHub, são realinhados por `pg_sync_shared_assets.ps1`
- scripts, documentação e restantes ativos do framework vivem em `.pg_framework/` e refletem imediatamente a versão atual do `_pg_template` quando a ligação local estiver saudável

Depois da sincronização, no GitHub do projeto:
- criar o secret `PG_TEMPLATE_REPO_TOKEN`
- opcionalmente definir `PG_TEMPLATE_REPO`
- opcionalmente definir `PG_TEMPLATE_REF`

Depois do sync, repetir o smoke test. O `pg_smoke_test_repo.ps1` passa a acusar drift quando `AGENTS.md`, `CLAUDE.md`, `config.toml`, workflow ou `doc_templates` ficarem desfasados do framework partilhado.

## Garantias esperadas

- source Odoo visível no projeto e fora do Git
- framework partilhado acessível via `.pg_framework/`
- versão e links oficiais sincronizados automaticamente no `PG_CONTEXT.md`
- âmbito inicial estruturado em `PG_SCOPE_INTAKE.yaml`
- snapshot de âmbito reservado em `.pg/PG_SCOPE_SYNC.json`
- workflow GitHub reservado para refresh remoto de `PG_CONTEXT.md`
- Codex e Claude disciplinados para decidir `standard -> modulo adicional -> Studio -> custom` a partir do mesmo contrato local
