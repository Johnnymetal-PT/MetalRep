# _pg_template - Bootstrap consultivo para repositorios Odoo

Ultima release fechada do template: `v2.9.1`

Estado operativo atual:
- backlog dominante atual desta ronda: `docs/PG_FRAMEWORK_IMPROVEMENT_BACKLOG.md`
- modelo dominante atual: `PG AI Assistant V1 mirror redesign`
- piloto V1 fechado formalmente com leitura `READY WITH GUARDRAILS`
- `Ronda 1 - Contrato minimo global` fechada em `2026-04-21`
- `Ronda 2 - Hygiene global` fechada em `2026-04-21`
- ronda ativa atual: `Ronda 3 - Segmentacao semantica conservadora`
- correcao de rumo da ronda ativa: `included_scope` passa a assumir-se como vista curada principal, nao como contentor unico de verdade factual
- a verdade factual relevante mas ainda insuficiente deixa de ser removida silenciosamente e passa a ser preservada como backlog factual pendente de curadoria
- o gestor do projeto passa a ter de ser sinalizado sobre o que existe no Odoo mas ainda nao esta suficientemente estruturado para entrar no `included_scope`
- proxima frente de implementacao dentro da ronda: separar `included_scope` curado de `factual_scope_backlog` e expor essa sinalizacao no espelho e no Odoo
- o ponto de entrada operativo atual fica consolidado em `docs/PG_CURRENT_WORKING_STATE.md`
- o backlog operativo dominante desta ronda fica consolidado em `docs/PG_FRAMEWORK_IMPROVEMENT_BACKLOG.md`
- os artefactos detalhados de rondas anteriores da linha `mirror transformation` nao estao presentes nesta snapshot e devem ser tratados como historico externo, nao como backlog ativo local
- a baseline `v2.9.0` e os documentos `V29` passam a valer como linha historica anterior, nao como backlog dominante atual

Este template prepara novos repositorios Odoo para dois objetivos em simultaneo:
- bootstrap tecnico consistente
- disciplina consultiva Odoo antes de qualquer decisao de desenvolvimento
- preparacao de intake estruturado e refresh factual do contexto a partir do estado do projeto
- referencia estavel ao framework partilhado a partir de cada projeto

O template deixa de ser apenas um guard-rail de desenvolvimento. Passa a obrigar o agente a validar primeiro configuracao standard, depois modulos standard adicionais, depois Studio e so por fim custom.

O suporte local ao Odoo Language Server e preparado por `scripts/pg_setup_odools.ps1`. O script gera um `odools.toml` local e ignorado pelo Git, resolvendo source e addon roots a partir de cada repositorio. A skill partilhada `pg-odoo-navigator` usa consultas limitadas e mantem leitura direta final obrigatoria; cold starts do OdooLS nao devem ser repetidos durante uma tarefa.

A skill partilhada `pg-revisao-sexta` conduz a revisao de sexta-feira de projetos Odoo: `scripts/pg_revisao_sexta.py` le o Odoo da Parametro Global (so leitura), gera a ficha da pessoa fora do repositorio e o agente percorre-a com ela, ponto a ponto (Parte A: o meu quadro; Parte B: os meus projetos). Ver `AGENTS_SHARED.md`, seccao "Revisao de sexta-feira".

## Principios base

- `vendor/odoo_src` e apenas referencia tecnica e e `read-only`
- o source Odoo nunca entra no Git
- tudo o que for criado no projeto usa prefixo `pg_` quando aplicavel
- o agente consulta sempre `PG_CONTEXT.md`, codigo do projeto, `vendor/odoo_src` e documentacao oficial da versao ativa
- o agente nao adivinha nem apresenta inferencias como factos
- o contexto funcional e decisorio vive no `PG_CONTEXT.md`
- `PG_SCOPE_INTAKE.yaml` e a fonte estruturada do ambito inicial do projeto
- `.pg/PG_SCOPE_SYNC.json` guarda snapshots factuais do ambito vivo do projeto
- `.pg/PG_EFFORT_SYNC.json` guarda snapshots factuais agregados de esforco (resumo operacional)
- o addon passa a expor um wizard de onboarding para ligar GitHub, projeto, repositorio e toggles principais num unico fluxo
- a task passa a expor um fluxo consultivo guiado por etapas para discovery, fit-gap, recomendacao final e gate
- o addon passa a expor um dashboard operacional centralizado para projetos com atencao, runs falhadas e tasks bloqueadas
- o projeto sinaliza quando o estado operacional mudou e ainda falta novo publish manual
- o fluxo AI da task exige `Consultive Gate` marcado como pronto antes de `Gerar Prompt AI` e `Executar com Codex`
- a task tem de registar classificacao consultiva final (`standard`, `modulo adicional`, `Studio`, `custom`) antes do fluxo AI
- o snapshot factual de scope inclui apenas tasks classificadas como `approved_scope`
- a task passa a suportar drafts heuristicas para `Scope Summary`, `Acceptance Criteria` e `Scope Kind`, mantendo-os separados dos campos oficiais ate aplicacao explicita
- o projeto passa a suportar geracao e aplicacao assistida em massa de drafts de scope para acelerar consolidacao brownfield
- o dashboard operacional passa a destacar o que ainda falta consolidar no brownfield antes de confiar no `scope sync`
- o draft operacional de status passa a considerar explicitamente backlog operacional, enriquecimento de scope em falta, drafts `needs_review` e runs com erro em cenarios brownfield
- a task passa a suportar drafts consultivos assistidos para `Recommendation Class`, reviews minimas e `Recommendation Justification`, mantendo sugestoes separadas da decisao final oficial
- a task mantem um trilho minimo de decisao consultiva para gate, prompt e trigger do Codex
- `.pg_framework/` e a referencia local ao framework partilhado
- a framework passa a integrar sinais filtrados do chatter de projeto e task como grounding auditavel para drafts de scope, status e consultoria
- o apoio LLM fica limitado a mensagens ambiguas do chatter, com JSON estrito, validacao forte e fallback deterministico

## Ordem obrigatoria de decisao

Antes de propor desenvolvimento custom, o agente tem de validar esta ordem:
1. standard ja existente no projeto
2. modulo standard adicional do Odoo, mesmo que nao esteja instalado
3. Odoo Studio
4. custom

Esta ordem e obrigatoria e aplica-se a analise funcional, consultoria e desenvolvimento.
A descoberta de modulos standard adicionais deve considerar sempre o `vendor/odoo_src` da versao ativa, incluindo modulos novos introduzidos pelo Odoo.

## Estrutura

```text
_pg_template/
|-- templates/   -> ficheiros copiados para cada projeto
|-- scripts/     -> bootstrap, clone/update do source Odoo, intake e sincronizacao do contexto
|-- docs/        -> documentacao de apoio
|                   -> ex: PG_DECISION_ENGINE_PROMPT.md (prompt para analise consultiva Odoo)
|-- vendor/      -> ligacoes locais para source Odoo em cache global da maquina
|-- .pg/         -> reservado para snapshots factuais locais ao projeto
|-- config.toml
`-- README.md
```

## Documentacao de apoio

Esta snapshot do repositorio nao inclui todos os artefactos historicos referidos no `CHANGELOG.md`.
Para trabalho operativo nesta copia local, usar apenas a documentacao realmente presente em `docs/` e o backlog dominante em `docs/PG_FRAMEWORK_IMPROVEMENT_BACKLOG.md`.

- `docs/PG_CURRENT_WORKING_STATE.md` - ponto de entrada operativo atual, com frente dominante, bloqueio principal e proximo passo logico
- `docs/PG_FRAMEWORK_IMPROVEMENT_BACKLOG.md` - backlog operativo dominante da ronda atual
- `docs/BRODOO_QUICK_START.md` - arranque rapido do addon e do espelho factual
- `docs/BRODOO_GUIA_OPERACIONAL.md` - referencia operacional do Brodoo para projeto, onboarding, mirror e syncs
- `docs/BRODOO_AGENTES_AI_GUIA.md` - contrato operativo de uso de Claude e Codex em repositorios espelhados
- `docs/PG_BOOTSTRAP_CHECKLIST.md` - checklist de bootstrap e validacao inicial
- `docs/PG_GLOBAL_DEV_SETUP.md` - setup global de desenvolvimento
- `docs/PG_IMPLEMENTATION_CONTINUITY_PROTOCOL.md` - protocolo de continuidade para implementacao, deploy, upgrade e validacao
- `docs/PG_TEMPLATE_USAGE_GUIDE.md` - guia de utilizacao corrente do template nesta snapshot
- `docs/PG_SCOPE_INTAKE_SPEC.md` - especificacao do ficheiro estruturado de ambito inicial
- `docs/PG_DISCOVERY_PROMPT.md` - apoio a discovery e qualificacao inicial
- `docs/PG_FIT_GAP_FRAMING_PROMPT.md` - apoio a enquadramento fit-gap
- `docs/PG_DECISION_ENGINE_PROMPT.md` - apoio a analise consultiva Odoo
- `docs/PG_CHALLENGER_PROMPT.md` - apoio a critica de propostas antes de implementacao
- `docs/PG_CONSULTING_DECISION_PATTERNS.md` - biblioteca leve de padroes consultivos
- `docs/PG_PRE_RESPONSE_CHECKLIST.md` - checklist curta antes de recomendacoes consultivas finais
- `docs/PG_PROJECT_LEARNINGS.md` - memoria de aprendizagens reutilizaveis
- `docs/PG_CONTENT_HYGIENE.md` - regras de coerencia textual e placeholders
- `docs/PG_SHARED_VS_LOCAL_MODEL.md` - fronteira entre o que fica no framework e o que fica local ao projeto
- `docs/PG_ODOOLS_ROLLOUT.md` - setup, rollout, testes e limites operacionais do Odoo Language Server
- `docs/PG_TEMPLATE_VERSIONING.md` - regras de versionamento do template
- `docs/PG_RELEASE_POLICY.md` - politica de release do `_pg_template`
- `docs/PG_TROUBLESHOOTING.md` - problemas recorrentes e resolucoes operacionais
- `CHANGELOG.md` - historico de releases e rondas anteriores

## Bootstrap de um novo repositorio

### Automático, na primeira sessão (recomendado)

Instala-se **uma vez por máquina**:

```powershell
py C:\CAMINHO\PARA\_pg_template\scripts\pg_install_user_hooks.py
```

Em macOS/Linux: primeiro o PowerShell (`brew install powershell` no macOS), depois `python3 <_pg_template>/scripts/pg_install_user_hooks.py` (o hook fica com `pwsh`). Sem `pwsh`, o instalador recusa-se a instalar e diz porquê: um hook sem PowerShell falharia em todas as sessões.

Isto regista o `scripts/pg_auto_bootstrap.ps1` como hook `SessionStart` **do utilizador** (`~/.claude/settings.json` e `~/.codex/hooks.json`), com o caminho absoluto do `_pg_template` desta máquina. A partir daí, basta clonar o repositório e abrir o Claude nele: se o repositório ainda não tiver a framework, o bootstrap corre sozinho.

O hook tem de ser do utilizador porque o ritual e os hooks do projeto vivem em `.pg_framework\scripts\` e em `.claude/settings.json`, que são criados **pelo** bootstrap. Num repositório por bootstrapar ainda não existem.

De onde vêm os dados, sem notas nem comandos a editar:

| Dado | Origem |
|---|---|
| nome e caminho | raiz git da pasta onde a sessão abriu |
| projeto, versão Odoo, edição, branch Brodoo | projeto do Brodoo ligado a este repositório GitHub (`pg_repository_id`) |
| versão, quando já está escrita | `PG_CONTEXT.md` ou `-Series`, que mandam sobre o Brodoo |

O que ele **não** faz, de propósito:
- **só bootstrapa repositórios ligados a um projeto no Brodoo.** O hook corre em qualquer repositório aberto nesta máquina, e um clone de um projeto qualquer não deve ganhar `AGENTS.md`, `.pg/` nem uma branch `brodoo` publicada. Sem projeto no Brodoo não faz nada; se o repositório estiver na pasta dos repos, o agente recebe o comando já preenchido para perguntar ao utilizador;
- **não adivinha a versão Odoo.** Se o Brodoo não a tiver, ou se dois projetos do mesmo repositório tiverem versões diferentes, faz o bootstrap da framework (que não depende da versão) e deixa o clone do source por fazer, com o motivo;
- **não clona gigabytes no arranque.** O source é global por série (`~/.pg/odoo_src/<serie>`). Se a série já estiver na máquina, liga-se sem fetch, em segundos. Se não estiver, o clone fica adiado e o agente recebe o comando para o correr em segundo plano;
- **não consulta o Brodoo com a chave partilhada.** A consulta é feita com a chave pessoal de quem está na máquina (`pg_init_odoo_credentials.ps1`), e fica atribuída a essa pessoa. Numa máquina que só tenha a chave do utilizador Brodoo, ou nenhuma, não consulta: diz como configurar a pessoal e não faz o bootstrap;
- não toca no próprio `_pg_template`, em pastas de trabalho (`PG_WORK_FOLDER`) nem em repositórios de produto (`brodoo_mirror_applicable: false`).

Os ficheiros de framework são escritos na branch Brodoo: o checkout do ritual corre antes do bootstrap e, se falhar, o bootstrap não corre. O detalhe fica em `~/.pg/logs/auto_bootstrap_<repo>_<data>.log`. Num repositório já bootstrapado o hook sai em cerca de 0,3 s, sem escrever nada.

Correr à mão, por exemplo para ver a decisão antes de a tomar:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\CAMINHO\PARA\_pg_template\scripts\pg_auto_bootstrap.ps1" -RepoPath "C:\CAMINHO\PARA\Repos\NOME_DO_REPO" -WhatIf
```

`-Series`/`-Edition` forçam a versão e a edição; `-SemBrodoo` bootstrapa um repositório sem projeto no Brodoo (decisão explícita de quem corre); `PG_AUTO_BOOTSTRAP=0` desliga o hook. Para retirar o hook: `py scripts\pg_install_user_hooks.py --remover`.

Os hooks do projeto só ficam ativos a partir da **sessão seguinte**. Na primeira, o agente segue o ritual à mão, como lhe é dito na saída do hook.

### Manual

Antes de correr os comandos abaixo, define o root real do template no teu ambiente:

```powershell
$TEMPLATE_ROOT = "C:\CAMINHO\PARA\_pg_template"
$REPOS_ROOT = "C:\CAMINHO\PARA\Repos"
Test-Path "$TEMPLATE_ROOT\scripts\pg_bootstrap_assisted.ps1"
```

Se o `Test-Path` devolver `False`, o path esta errado e tens de o corrigir antes de continuar.

Regra pratica:
- o `TEMPLATE_ROOT` tem de ser a pasta que contem este `README.md` e a pasta `scripts/`
- num clone normal do GitHub (`git clone ...`), isso costuma ser `...\_pg_template`
- um caminho `...\_pg_template\_pg_template` so acontece quando o clone foi feito dentro de uma pasta pai que ja tinha o mesmo nome

### Fluxo curto recomendado

Para um arranque assistido, usar:

```powershell
cd $TEMPLATE_ROOT
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\pg_bootstrap_assisted.ps1" -RepoName "NOME_DO_REPO" -RepoPath "$REPOS_ROOT\NOME_DO_REPO" -CloneOdooSource -Series 19.0 -Edition enterprise
```

O script:
- cria o diretorio do repositorio se ainda nao existir
- inicializa Git localmente quando necessario
- aplica bootstrap
- sincroniza os assets partilhados
- clona o source Odoo quando pedido
- corre o smoke test final

### 1. Aplicar o template ao repositorio

```powershell
cd $TEMPLATE_ROOT
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\pg_bootstrap_repo.ps1" -RepoName "NOME_DO_REPO" -RepoPath "$REPOS_ROOT\NOME_DO_REPO"
```

O bootstrap copia, por omissao, se ainda nao existirem:
- `.editorconfig`
- `AGENTS.md`
- `CLAUDE.md`
- `PG_CONTEXT.md`
- `PG_SCOPE_INTAKE.yaml`
- `config.toml`
- `.gitignore`
- `.gitattributes`
- `.github/workflows/pg_refresh_pg_context.yml`
- `.pg/PG_SCOPE_SYNC.json`
- `.pg/PG_EFFORT_SYNC.json`
- `.pg/tokens/consumption.jsonl`

Comportamento de preservacao (default):
- se `PG_CONTEXT.md` e `PG_SCOPE_INTAKE.yaml` ja existirem, o bootstrap nao reescreve esses conteudos
- a materializacao automatica do contexto a partir do intake e ignorada quando ambos ja existiam, para evitar perda de informacao local
- para reposicao forçada, usar `-Force`

Tambem garante as pastas `vendor/` e `.pg/` e cria `.pg_framework/` como referencia local ao framework partilhado.
Os scripts do template passam tambem a escrever ficheiros textuais em UTF-8 explicito para reduzir risco de corrupcao de acentos no Windows.

### 2. Preparar o source Odoo por git clone

O `odoo/enterprise` e um repositorio privado — precisas de acesso e de ter as credenciais GitHub configuradas. O Windows usa o Git Credential Manager por omissao; se ainda nao estiver configurado, o git vai pedir username e Personal Access Token (scope `repo`) na primeira vez e guarda automaticamente.

```powershell
cd $TEMPLATE_ROOT
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\pg_clone_odoo_source.ps1" -RepoName "NOME_DO_REPO" -RepoPath "$REPOS_ROOT\NOME_DO_REPO" -Series "19.0" -Edition "enterprise"
```

Exemplos:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\pg_clone_odoo_source.ps1" -RepoName "cliente_x" -RepoPath "$REPOS_ROOT\cliente_x" -Series "19.0" -Edition "community"
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\pg_clone_odoo_source.ps1" -RepoName "cliente_x" -RepoPath "$REPOS_ROOT\cliente_x" -Series "19.0" -Edition "enterprise"
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\pg_clone_odoo_source.ps1" -RepoName "cliente_x" -RepoPath "$REPOS_ROOT\cliente_x" -Series "19e"
```

O script:
- cria ou atualiza um cache global por serie em `%USERPROFILE%\.pg\odoo_src\<SERIE>\community`
- cria ou atualiza tambem `%USERPROFILE%\.pg\odoo_src\<SERIE>\enterprise` quando a edicao for `enterprise`
- cria ou atualiza `vendor/odoo_src` no repo como ligacao para o cache global da serie
- usa os repositorios oficiais `odoo/odoo` e, quando houver acesso, `odoo/enterprise`
- atualiza o `PG_CONTEXT.md` com versao, paths do source e links oficiais da documentacao dessa versao

O script legado `scripts/pg_link_odoo_core.cmd` continua disponivel apenas como wrapper de compatibilidade, mas o fluxo recomendado passa a ser sempre `pg_clone_odoo_source`.

### 3. Confirmar os pontos de decisao antes de trabalhar

No repositorio bootstrapado, confirmar e preencher:
- `PG_SCOPE_INTAKE.yaml`
- versao do Odoo
- edicao
- ambiente
- restricoes contratuais
- pedido funcional atual
- processo atual
- dor e impacto de negocio

Depois materializar o contexto inicial:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\pg_build_pg_context.ps1" -RepoPath "$REPOS_ROOT\NOME_DO_REPO"
```

Sem estes pontos, o template obriga o agente a pedir clarificacao antes de concluir.

### 4. Verificar o estado do repositorio

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\pg_smoke_test_repo.ps1" -RepoPath "$REPOS_ROOT\NOME_DO_REPO"
```

Todos os `OK` e sem erros significa que o repositorio esta operacional. Os `WARN` sobre snapshots placeholder ou source Odoo em falta sao normais nesta fase.

## Bootstrap em Linux / macOS

Os scripts sao os mesmos. A unica diferenca e o comando de invocacao: usa `pwsh` em vez de `powershell`, e nao e necessario `Set-ExecutionPolicy`.

### Pre-requisito: PowerShell Core

```bash
# Ubuntu / Debian / Linux Mint
sudo apt-get install -y wget
wget -q "https://packages.microsoft.com/config/ubuntu/22.04/packages-microsoft-prod.deb"
sudo dpkg -i packages-microsoft-prod.deb
sudo apt-get update -q && sudo apt-get install -y powershell
rm packages-microsoft-prod.deb

# macOS (Homebrew)
brew install --cask powershell
```

Verificar a instalacao:

```bash
pwsh --version
```

### Definir os paths de base

```bash
TEMPLATE_ROOT="/CAMINHO/PARA/_pg_template"
REPOS_ROOT="/CAMINHO/PARA/Repos"
pwsh -Command "Test-Path '$TEMPLATE_ROOT/scripts/pg_bootstrap_assisted.ps1'"
```

Se devolver `False`, o path esta errado.

### Fluxo curto recomendado

```bash
cd "$TEMPLATE_ROOT"
pwsh scripts/pg_bootstrap_assisted.ps1 -RepoName "NOME_DO_REPO" -RepoPath "$REPOS_ROOT/NOME_DO_REPO" -CloneOdooSource -Series 19.0 -Edition enterprise
```

### 1. Aplicar o template ao repositorio

```bash
cd "$TEMPLATE_ROOT"
pwsh scripts/pg_bootstrap_repo.ps1 -RepoName "NOME_DO_REPO" -RepoPath "$REPOS_ROOT/NOME_DO_REPO"
```

### 2. Preparar o source Odoo por git clone

O `odoo/enterprise` e um repositorio privado — precisas de acesso e de ter as credenciais GitHub configuradas. Faz isto uma vez na maquina antes de correr o script:

```bash
git config --global credential.helper store
```

Na primeira vez que o clone pedir credenciais, usa o teu username GitHub e um Personal Access Token (scope `repo`) como password. O git guarda e nao volta a pedir.

```bash
cd "$TEMPLATE_ROOT"
pwsh scripts/pg_clone_odoo_source.ps1 -RepoName "NOME_DO_REPO" -RepoPath "$REPOS_ROOT/NOME_DO_REPO" -Series "19.0" -Edition "enterprise"
```

O cache global fica em `~/.pg/odoo_src/<SERIE>/` (equivalente a `%USERPROFILE%\.pg\odoo_src\<SERIE>\` no Windows). Para projetos seguintes com a mesma serie o clone ja nao e repetido — so e criado o link `vendor/odoo_src`.

### 3. Confirmar os pontos de decisao antes de trabalhar

```bash
pwsh scripts/pg_build_pg_context.ps1 -RepoPath "$REPOS_ROOT/NOME_DO_REPO"
```

### 4. Verificar o estado do repositorio

```bash
pwsh scripts/pg_smoke_test_repo.ps1 -RepoPath "$REPOS_ROOT/NOME_DO_REPO"
```

Todos os `OK` e sem erros significa que o repositorio esta operacional. Os `WARN` sobre snapshots placeholder ou source Odoo em falta sao normais nesta fase.

### Sincronizar um repositorio ja bootstrapado

```bash
cd "$TEMPLATE_ROOT"
pwsh scripts/pg_sync_shared_assets.ps1 -RepoName "NOME_DO_REPO"
```

### Notas de compatibilidade

- O `.pg_framework/` e criado como symlink no Linux/macOS e como Junction no Windows. Para garantir que o Git ignore corretamente ambos os casos, o `.gitignore` do template usa paths ancorados sem `/` final para `/.pg_framework` e `/vendor/odoo_src`.
- O `~/.claude/CLAUDE.md` global e criado automaticamente pelo bootstrap se ainda nao existir.
- Todos os outros scripts do template funcionam sem alteracoes com `pwsh`.

## Scripts incluidos

- `scripts/pg_bootstrap_repo.ps1`: aplica o template a um repositorio
- `scripts/pg_link_framework.ps1`: cria ou atualiza `.pg_framework/` para apontar para o framework partilhado
- `scripts/pg_clone_odoo_source.ps1`: faz clone ou update do source Odoo oficial em cache global por serie, cria ligacao `vendor/odoo_src` no repo e sincroniza o `PG_CONTEXT.md`
- `scripts/pg_clone_odoo_source.cmd`: wrapper para uso rapido em CMD
- `scripts/pg_init_scope_intake.ps1`: inicializa ou preenche o `PG_SCOPE_INTAKE.yaml`
- `scripts/pg_build_pg_context.ps1`: semeia blocos auto-geridos do `PG_CONTEXT.md` a partir do intake
- `scripts/pg_validate_scope_sync.ps1`: valida o contrato do snapshot factual de ambito antes de o aplicar
- `scripts/pg_apply_scope_sync.ps1`: aplica o ultimo snapshot factual de `.pg/PG_SCOPE_SYNC.json` ao `PG_CONTEXT.md`
- `scripts/pg_validate_effort_sync.ps1`: valida o contrato do snapshot factual agregado de esforco publicado
- `scripts/pg_log_token_consumption.ps1`: regista checkpoints de consumo de tokens (`session_open`, `session_progress`, `session_close`) em `.pg/tokens/consumption.jsonl`
- `scripts/pg_validate_token_consumption.ps1`: valida formato e consistencia do log de tokens em `.pg/tokens/consumption.jsonl`
- `scripts/pg_refresh_pg_context.ps1`: orquestra a aplicacao de scope sync e fallback de intake
- `scripts/pg_link_odoo_core.ps1`: wrapper legado que redireciona para o fluxo novo baseado em `git clone`
- `scripts/pg_link_odoo_core.cmd`: wrapper legado para uso rapido em CMD
- `scripts/pg_sync_pg_context.ps1`: deteta a versao do Odoo no source checkout e atualiza metadados no `PG_CONTEXT.md`
- `scripts/pg_smoke_test_repo.ps1`: smoke test estrutural e semantico minimo da framework, snapshots `.pg`, blocos `PG_AUTO` do `PG_CONTEXT.md`, log de tokens e higiene textual basica
- `scripts/pg_run_odoo_addon_tests.ps1`: executa instalacao, upgrade e suite automatizada minima do addon `pg_brodoo` em Odoo 19 local
- `scripts/pg_sync_shared_assets.ps1`: sincroniza ficheiros partilhados do template para repositorios ja bootstrapados, sem tocar no estado local do projeto
- `scripts/pg_bootstrap_assisted.ps1`: agrega bootstrap, sync de assets, clone opcional do source Odoo e smoke test final
- `scripts/pg_align_fleet_framework.ps1`: alinha os ficheiros geridos pela framework em toda a frota e publica na branch Brodoo de cada repositorio. Audit-first (sem `-Apply` nada e escrito). Salta repositorios que declarem `main`, que nao declarem branch Brodoo ou que tenham commits locais nao publicados fora do ambito da framework, e nunca faz stage de `.pg/projects/**`, `projects/**` ou `PG_CONTEXT.md`, que pertencem ao publisher do espelho
- `scripts/pg_test_align_fleet_framework.ps1`: testes deterministas do alinhador, sobre uma frota falsa em pasta temporaria (nao toca em repositorios reais nem na rede)
- `scripts/pg_test_untrack_local_state.ps1`: testes do desversionamento de estado local (`.pg/PREFLIGHT.json`) feito pelo sync

Compatibilidade de agentes:
- Codex usa `AGENTS.md` como instrucoes locais do projeto.
- Claude Code usa `CLAUDE.md` como memoria de projeto.
- O `CLAUDE.md` do template importa `AGENTS.md` e `.pg_framework/templates/AGENTS_SHARED.md`, para evitar divergencia entre agentes.

Sincronizacao de assets partilhados:
- `scripts/pg_sync_shared_assets.ps1` sincroniza os ficheiros copiados para repositorios bootstrapados e atualiza `.pg/PG_TEMPLATE_SYNC_STATE.json`
- `scripts/pg_smoke_test_repo.ps1` passa a detetar drift entre os assets locais do repo e o framework partilhado acessivel via `.pg_framework`
- `scripts/pg_align_fleet_framework.ps1` fecha o ciclo na frota: o publisher do espelho escreve `.pg/projects/**` e `projects/**`, mas **nunca** os ficheiros da framework, pelo que a cada release do `_pg_template` os repositorios ficam desalinhados ate alguem correr o sync e publicar

Na baseline atual, os projetos bootstrapados passam tambem a receber um workflow GitHub que consegue regenerar `PG_CONTEXT.md` quando os snapshots `.pg` mudam no remoto.
Ver `templates/.github/workflows/pg_refresh_pg_context.yml`.

Exemplo rapido para correr os testes automatizados minimos do addon:

```powershell
powershell -ExecutionPolicy Bypass -File "$TEMPLATE_ROOT\scripts\pg_run_odoo_addon_tests.ps1"
```

## Publicar o proprio `_pg_template`

O `_pg_template` deve existir tambem como repositorio Git versionado.
Depois de criares o remoto, o fluxo minimo e este:

```powershell
cd $TEMPLATE_ROOT
git remote add origin URL_DO_REPO
git push -u origin main
```

Se o remoto ja existir:

```powershell
cd $TEMPLATE_ROOT
git remote -v
git push origin main
```

Recomendacao:

- manter `main` como branch de referencia da framework
- tratar `_pg_template` como source of truth
- so propagar para projetos bootstrapados o que ja foi consolidado no template

A politica de release da framework esta formalizada em `docs/PG_RELEASE_POLICY.md`.
A ultima release fechada e `v2.21.2`, e a linha operativa atual fica ancorada em `docs/PG_CURRENT_WORKING_STATE.md` e `docs/PG_FRAMEWORK_IMPROVEMENT_BACKLOG.md`.
Os documentos `V29` e outros artefactos historicos citados no `CHANGELOG.md` devem ser tratados apenas como contexto historico quando nao estiverem presentes nesta snapshot local.

## O que o template passa a impor

- raciocinio consultivo antes de coding
- avaliacao obrigatoria de modulos standard adicionais
- consulta obrigatoria a `PG_CONTEXT.md`, codigo do projeto, `vendor/odoo_src` e documentacao oficial da mesma versao
- classificacao final da recomendacao
- justificacao explicita quando standard ou Studio nao chegam
- separacao entre `FACTO OBSERVADO`, `INFERENCIA` e `PONTO POR VALIDAR`

## Exemplo de decisao consultiva esperada

Pedido: "queremos aprovacoes multi-etapa em compras"

Fluxo esperado:
1. verificar se o projeto ja usa aprovacoes standard de compras
2. avaliar modulos standard adicionais relacionados com approvals, purchase ou studio-supported automation
3. avaliar se Studio cobre o gap sem risco contratual ou de upgrade excessivo
4. so depois propor custom, com justificacao e paths do source consultados

## Regras nao opcionais

- nunca alterar `vendor/odoo_src`
- nunca versionar o source Odoo
- nunca recomendar custom sem justificar porque as opcoes anteriores falham
- nunca fechar conclusoes com base em suposicoes
- manter `PG_CONTEXT.md` alinhado com a decisao atual do projeto
