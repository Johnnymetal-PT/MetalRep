# PG_TROUBLESHOOTING

## Objetivo
Este documento regista problemas reais encontrados durante a validação do piloto e a forma correta de os resolver sem improviso.

## 1. Scripts não existem em `.\scripts\` no repositório bootstrapado

**Sintoma**
- o guia ou o utilizador tenta correr `.\scripts\pg_refresh_pg_context.ps1`
- o projeto bootstrapado não tem pasta `scripts` na raiz

**Causa**
- os scripts operacionais vivem em `.pg_framework/scripts/`
- o bootstrap cria uma referência local ao framework partilhado, não uma copia integral da pasta `scripts`

**Resolução**
- usar `.\.pg_framework\scripts\...`
- ou correr os scripts a partir do próprio `_pg_template` apontando `-RepoPath`

**Exemplo**
```powershell
powershell -ExecutionPolicy Bypass -File C:\Users\Utilizador\Desktop\Repos\brodoo_v2\.pg_framework\scripts\pg_refresh_pg_context.ps1 -RepoPath 'C:\Users\Utilizador\Desktop\Repos\brodoo_v2'
```

## 2. Placeholder `.pg/PG_SCOPE_SYNC.json` não passa no validator

**Sintoma**
- `pg_validate_scope_sync.ps1` falha logo após bootstrap

**Causa**
- o ficheiro bootstrapado e apenas placeholder
- o validator espera um snapshot real publicado pelo Odoo

**Resolução**
- não usar o validator diretamente sobre o placeholder inicial
- primeiro publicar um snapshot real a partir do Odoo
- no refresh normal, o script já faz fallback para o intake quando não existe snapshot valido

## 3. PowerShell bloqueia scripts com `ExecutionPolicy`

**Sintoma**
- erro `running scripts is disabled on this system`

**Causa**
- politica local do PowerShell no Windows

**Resolução**
- correr o script com `ExecutionPolicy Bypass`

**Exemplo**
```powershell
powershell -ExecutionPolicy Bypass -File C:\Users\Utilizador\Desktop\Repos\brodoo_v2\.pg_framework\scripts\pg_refresh_pg_context.ps1 -RepoPath 'C:\Users\Utilizador\Desktop\Repos\brodoo_v2'
```

## 4. Odoo 19 rejeita `numbercall` em `ir.cron`

**Sintoma**
- build falha com `ValueError: Invalid field 'numbercall' in 'ir.cron'`

**Causa**
- Odoo 19 removeu esse campo do modelo `ir.cron`

**Resolução**
- remover `numbercall` do XML
- definir explicitamente `user_id` no cron quando necessário

## 5. Campo `PG Repository` gera RPC error em `name_search`

**Sintoma**
- abrir o many2one de repositório rebenta com erro no servidor

**Causa**
- em Odoo 19, `name_search` usa `domain` e não `args` na chamada ao `super()`

**Resolução**
- alinhar o override com a assinatura e chamada corretas de Odoo 19

## 6. Falta de `GitHub Token` no Odoo

**Sintoma**
- ao tentar escolher repositório ou sincronizar conta GitHub aparece erro `Configuracao em falta: GitHub Token.`

**Causa**
- token GitHub não configurado no `Settings`

**Resolução**
- criar um fine-grained personal access token no GitHub
- configurar pelo menos permissões de `Contents` e `Pull requests`
- colar no campo `GitHub Token`
- correr `Importar e Sync GitHub`

## 7. `https://github.com/odoo/enterprise` devolve `404`

**Sintoma**
- clone ou abertura do repositório devolve `Repository not found`

**Causa**
- o repositório existe, mas e privado
- a conta GitHub atual não tem acesso efetivo

**Resolução**
- para parceiros: garantir que o username GitHub foi associado corretamente no lado Odoo e que o convite foi aceite
- para não parceiros: usar o bundle oficial de download Enterprise em vez de GitHub

## 8. Repositório bootstrapado continua desfasado do template

**Sintoma**
- projeto piloto tem `AGENTS.md`, `.gitignore`, `config.toml` ou addon em versões antigas

**Causa**
- bootstrap inicial não reaplica alterações transversais posteriores

**Resolução**
- correr `pg_sync_shared_assets.ps1`
- confirmar que `.pg/PG_TEMPLATE_SYNC_STATE.json` ficou atualizado
- repetir `pg_smoke_test_repo.ps1` para validar que o drift foi removido
- lembrar que o sync cobre apenas os assets bootstrapados para a raiz; scripts e docs do framework são consumidos via `.pg_framework/`

**Exemplo**
```powershell
powershell -ExecutionPolicy Bypass -File C:\Users\Utilizador\Desktop\Repos\_pg_template\scripts\pg_sync_shared_assets.ps1 -RepoName brodoo_v2
```

## 9. Repositório bootstrapado precisa de validação rapida

**Sintoma**
- duvida sobre estrutura mínima, snapshots, source Odoo ou addon

**Resolução**
- correr `pg_smoke_test_repo.ps1`
- se aparecerem warnings de drift de assets partilhados, correr primeiro `pg_sync_shared_assets.ps1`

**Exemplo**
```powershell
powershell -ExecutionPolicy Bypass -File C:\Users\Utilizador\Desktop\Repos\_pg_template\scripts\pg_smoke_test_repo.ps1 -RepoPath C:\Users\Utilizador\Desktop\Repos\brodoo_v2 -RequireOdooSource -CheckPgAiDevAssistant
```

## 10. Acentos corrompidos em `PG_CONTEXT.md`

**Sintoma**
- texto com caracteres partidos ou mojibake após refresh

**Causa**
- escrita implicita com encoding errado em Windows

**Resolução**
- usar os scripts atuais do template, que já escrevem em UTF-8 explicito
- manter `.editorconfig` e `.gitattributes` sincronizados
- se necessário, regenerar o contexto a partir dos snapshots

## 11. Build Odoo.sh com `Warning` mas sem falha funcional

**Sintoma**
- estado `Test: Warning` no Odoo.sh

**Causa**
- warnings de labels duplicadas, deprecations ou ruido não fatal

**Resolução**
- abrir os logs de update e confirmar se existem `ERROR`, `CRITICAL` ou `Traceback`
- se o módulo carregar e o fluxo funcional estiver correto, tratar warnings documentais separadamente

## 12. Workflow GitHub não regenera `PG_CONTEXT.md`

**Sintoma**
- os snapshots `.pg` mudam no GitHub, mas `PG_CONTEXT.md` não e atualizado automaticamente

**Causas tipicas**
- workflow `.github/workflows/pg_refresh_pg_context.yml` em falta no projeto
- secret `PG_TEMPLATE_REPO_TOKEN` não configurado
- token sem acesso de leitura ao `_pg_template`
- variáveis `PG_TEMPLATE_REPO` ou `PG_TEMPLATE_REF` com valor incorreto

**Resolução**
- sincronizar os assets partilhados do template para garantir que o workflow existe
- criar ou atualizar o secret `PG_TEMPLATE_REPO_TOKEN`
- validar manualmente o workflow com `workflow_dispatch`
- se necessário, correr refresh local como fallback diagnostico

**Referência**
- ver `templates/.github/workflows/pg_refresh_pg_context.yml`

## Cópia local do `pg_brodoo` — não é a fonte do que está deployado

`_pg_template/pg_brodoo/` é um **espelho**, não a fonte de verdade do módulo. Serve de alvo de teste: o `pg_run_odoo_addon_tests.ps1` corre `-i pg_brodoo --test-tags /pg_brodoo` contra esta cópia, e o `pg_smoke_test_repo.ps1` valida-lhe o manifest. Um espelho desactualizado significa testar código que não é o que está deployado.

**Sincronizado a 27/07/2026** a partir de `parametro-odoo/Parametro_Global` (branch `brodoo`), de `19.0.1.9.0` para `19.0.1.13.0` — estava quatro versões menor atrás e carregava 13 ficheiros que a produção já tinha removido.

Editar o espelho e bumpar a versão produz duas consequências más: um **fork silencioso** (as alterações nunca chegam a produção) e, se alguém deployar a partir daqui, uma **regressão** que perde o que entrou entretanto na fonte.

Antes de alterar qualquer coisa em `pg_brodoo`:

1. confirmar a versão realmente instalada:
   `... -File scripts\pg_odoo_query.ps1 -Model ir.module.module -Method search_read -Domain '[["name","=","pg_brodoo"]]' -Fields "name,state,installed_version"`
   *(nota: com `powershell -File`, um domínio com aspas interiores é destruído pelo parser da linha de comandos — invocar o script directamente, sem `-File`)*
2. se a versão instalada for superior à local, **parar**: a alteração pertence à fonte real (repositório que o Odoo.sh da Parâmetro segue), não a esta cópia;
3. a fonte real é o repositório abaixo — a alteração pertence lá, não a esta cópia.

### Fonte real do `pg_brodoo` (confirmada 27/07/2026)

| | |
|---|---|
| Projeto Odoo.sh | `parametroglobal` |
| Repositório | `parametro-odoo/Parametro_Global` (com submódulos) |
| Branch de produção | `main` |
| Branch de staging | `brodoo` |

```
git clone --recurse-submodules --branch brodoo git@github.com:parametro-odoo/Parametro_Global.git
```

Obtém-se este comando no Odoo.sh, em qualquer branch, no painel **Connect** → **Clone** — **não** é preciso acesso a *Settings*.

Sequência para alterar o módulo: alterar na branch `brodoo` → o Odoo.sh reconstrói a staging com cópia dos dados de produção → validar → merge para `main` → reconstrução de produção com atualização do módulo. **Subir a versão no `__manifest__.py`**, senão os valores novos de uma `Selection` podem não sincronizar para `ir.model.fields.selection`.

`PONTO POR VALIDAR`: o acesso a este repositório é por convite na organização `parametro-odoo`. A conta `nuno-oliveira-pg` tem acesso ao Odoo.sh mas **não** ao repositório no GitHub (404 na API, e sem chave SSH registada nesta máquina). Quem precisar de alterar o módulo tem de pedir acesso primeiro.

## Regra prática final
- primeiro distinguir erro fatal de warning
- depois confirmar se o problema e do projeto piloto ou do `_pg_template`
- se for transversal, corrigir obrigatoriamente no `_pg_template` e só depois propagar para repositórios bootstrapados
