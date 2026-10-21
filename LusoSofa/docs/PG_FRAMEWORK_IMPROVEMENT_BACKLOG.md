# PG_FRAMEWORK_IMPROVEMENT_BACKLOG

## Objetivo

Formalizar o backlog filtrado das próximas ações de melhoria da framework, distinguindo:

- frentes aceites para execução
- frentes que exigem reformulação antes de implementação
- frentes a adiar por impacto arquitetural

Este documento serve como backlog operativo desta ronda.

## Regra de leitura

Cada item abaixo fixa:

- `ID`
- `Objetivo`
- `Decisao`
- `Racional`
- `Dependencias`
- `Impacto tecnico`
- `Criterios de aceitacao`

## Sequência recomendada

1. `BLK-000`
2. `PG-001`
3. `PG-002`
4. `PG-003`
5. `PG-004`
6. `PG-005`
7. `PG-006`
8. `PG-007`
9. `PG-008`
10. `PG-009`
11. `PG-010`

## Estado operacional da ronda

- `BLK-000`: `FECHADO`
- `PG-001`: `FECHADO`
- `PG-002`: `FECHADO`
- `PG-003`: `FECHADO`
- `PG-004`: `FECHADO (OPERACIONALIZACAO T3/T5/T6 CONCLUIDA EM 2026-05-27)`
- `PG-005`: `ADIADO (CONTRATO APROVADO EM 2026-05-27; AGUARDA REPO PILOTO + CONFIRMACAO ESFORCO F1)`
- `PG-006`: `FECHADO (SCRIPT EM PRODUCAO; PASSO 1 DO RITUAL OBRIGATORIO)`
- `PG-007`: `EM CURSO (F1 IMPLEMENTADO EM 2026-08-11; AGUARDA DEPLOY + REPUBLICACAO DOS ESPELHOS; D1/D2 EM ABERTO PARA F2)`

## Matriz curta de agentes AI

| Item | Agente principal | Modelo | Agente secundario | Fase recomendada |
|---|---|---|---|---|
| `BLK-000` | Claude Code | `opusplan` | Codex | `discovery + consolidacao documental`; passar a Codex na execução das correções documentais |
| `PG-001` | Codex | `gpt-5.2-codex` | Claude Code | `implementacao direta` |
| `PG-002` | Codex | `gpt-5.2-codex` | Claude Code | `discovery tecnico curto + implementacao` |
| `PG-003` | Codex | `gpt-5.2-codex` | Claude Code | `implementacao de engenharia` |
| `PG-004` | Claude Code | `opusplan` | Codex | `discovery arquitetural`; passar a Codex na integração API e materialização local |
| `PG-005` | Claude Code | `opusplan` | Codex | `discovery e contrato arquitetural`; adiar implementação até aprovação do modelo |
| `PG-007` | Claude Code | `opus-5` | Codex | `discovery e contrato arquitetural` (feito); passar a Codex na implementação de F1 (schema + preflight + testes) e F2 (modelo + recolha) |

## Itens

### BLK-000 - Consolidar contrato documental e estado operativo da framework

`ID`: `BLK-000`

`Objetivo`:
Consolidar o contrato documental e o ponto de entrada operativo da framework para que o estado atual, os paths publicados e as próximas frentes fiquem explicitos e coerentes.

`Decisao`:
`ACEITAR`

`Estado`:
`FECHADO`

`Racional`:
O repositório tem divergências entre documentação e implementação real. Isto reduz confianca no backlog e aumenta risco de decisões tomadas contra documentação desatualizada.

`Dependencias`:
Nenhuma. Deve acontecer antes das restantes frentes.

`Impacto tecnico`:
Atualização de `README`, guias operacionais, referências a backlog e roadmap e documentação dos artefactos `.pg`. Pode implicar criação do documento operativo em falta que passe a ser a source of truth da linha atual.

`Criterios de aceitacao`:
- o estado operativo atual fica definido num único ponto de entrada
- deixam de existir referências ativas a documentos inexistentes sem nota explicita
- os paths documentados para snapshots e mirror correspondem ao publisher real
- um operador novo consegue perceber a linha atual da framework sem depender de contexto oral

### PG-001 - Endurecer instruções dos agentes para considerar atalhos locais relevantes

`ID`: `PG-001`

`Objetivo`:
Endurecer as instruções dos agentes para considerarem sempre atalhos locais relevantes do repo atual, incluindo `vendor/odoo_src`, junctions e symlinks úteis para validação factual.

`Decisao`:
`ACEITAR`

`Estado`:
`FECHADO`

`Racional`:
A framework já exige consulta de `vendor/odoo_src`, mas a regra ainda esta demasiado centrada em ficheiros normais do repo. Falta explicitar a descoberta de fontes acessíveis via atalhos locais.

`Dependencias`:
- `BLK-000`

`Impacto tecnico`:
Atualização de `templates/AGENTS.md`, `templates/AGENTS_SHARED.md`, `templates/CLAUDE.md` e documentação operacional. Não exige alteração do modelo de dados nem dos syncs atuais.

`Criterios de aceitacao`:
- as instruções passam a referir explicitamente atalhos locais relevantes do repo atual
- `vendor/odoo_src` continua documentado como caso obrigatório quando aplicável
- o contrato dos agentes distingue `repo atual` de `apenas ficheiros versionados diretamente`
- a documentação de uso com agentes fica alinhada com esta regra

### PG-002 - Melhorar registo de consumo de tokens com checkpoints intermedios

`ID`: `PG-002`

`Objetivo`:
Melhorar o registo de consumo de tokens para produzir telemetria útil mesmo quando a sessão não chega ao fim lógico da tarefa.

`Decisao`:
`REFORMULAR`

`Estado`:
`FECHADO`

`Racional`:
O problema e real, mas hoje existe apenas como instrução comportamental. Isso não garante cobertura. O backlog deve assumir checkpoints intermedios e modo degradado, e não apenas registo final.

`Dependencias`:
- `BLK-000`
- recomendável depois de `PG-001`

`Impacto tecnico`:
Revisão do contrato em `AGENTS_SHARED`, definição de esquema de eventos em `.pg/tokens/consumption.jsonl` e eventual automação complementar via scripts ou integração no fluxo operacional.

`Criterios de aceitacao`:
- existe formato explicito para registo de abertura, progresso e fecho de sessão
- uma sessão interrompida deixa pelo menos um registo útil
- o ficheiro de consumo suporta multiplas entradas por sessão quando necessário
- a documentação distingue estimativa manual de medição automática, se esta não existir

### PG-003 - Publicar sync factual de esforco e tempos para `.pg`

`ID`: `PG-003`

`Objetivo`:
Publicar esforco factual do projeto em `.pg` através de um sync dedicado de tempos, com arranque em resumo operacional e não em detalhe bruto.

`Decisao`:
`REFORMULAR`

`Estado`:
`FECHADO`

`Racional`:
O mirror já inclui horas agregadas em projeto e task. Antes de adicionar timesheets detalhadas, e preciso definir o ganho real para contexto AI e evitar ruido, volume excessivo e exposição de detalhe desnecessario.

`Dependencias`:
- `BLK-000`
- validação funcional sobre dependências Odoo de timesheets

`Impacto tecnico`:
Possível extensão do addon para novos modelos e dados de esforco, novo snapshot `.pg`, novos validadores, documentação e testes. Pode implicar alteração das dependências do módulo para além de `project`.

`Criterios de aceitacao`:
- o backlog define explicitamente se o sync e resumo ou detalhe
- existe novo artefacto `.pg` para esforco factual com contrato mínimo estável
- o contexto AI consegue inferir carga, progresso e desvios com base nesse snapshot
- a solução evita publicar volume transacional desnecessario por defeito

### PG-004 - Centralizar templates documentais no Odoo Knowledge com source of truth editorial

`ID`: `PG-004`

`Objetivo`:
Centralizar a gestão documental de templates no Odoo Knowledge da Parâmetro Global, usando o Odoo como source of truth editorial.

`Decisao`:
`REFORMULAR`

`Estado`:
`FECHADO (T1/T2/T3/T5/T6 CONCLUIDOS E VALIDADOS EM 2026-05-27)`

`Discovery arquitetural`:
Fechado em 2026-05-26. Plano completo em `C:\Users\Utilizador\.claude\plans\objetivo-iniciar-e-fechar-parallel-donut.md`. Decisões arquiteturais fechadas: pull-based local cache com manifesto committed; destino `doc_templates/` committed; trigger manual + cron drift-check semanal; markdown raw em field Text no Odoo (lossless); cliente RPC em `scripts/`.

`Fase 0` (humana, fora do template):
Preparação detalhada em `docs/PG_004_FASE_0_PREPARATION.md`. Inclui spec do addon Odoo `pg_doc_templates`, spec do workspace e dos 6 articles a carregar, resolução técnica fundamentada dos PONTOS POR VALIDAR #1-#3 e #5 e #7, e checklist de fecho. Decisões de governance fechadas em 2026-05-26: #4 (workflow editorial) = 2-eyes desde o inicio, com exceção operacional apenas para bootstrap; #6 (frequência editorial) = ad-hoc com drift-check semanal. Execução no Odoo externo ainda pendente.

`Trabalho local ja adiantado`:
`docs/PG_004_FASE_0_PREPARATION.md`, `docs/PG_DOC_TEMPLATES_VERSIONING.md`.

`Implementacao tecnica ja concluida (repo _pg_template)`:
- `scripts/pg_doc_templates_common.py` (cliente JSON-RPC Odoo Knowledge; pull de artigos publicados + attachments).
- `scripts/pg_pull_doc_templates.ps1` (staging atomico, promote em sucesso total, abort/cleanup em falha parcial, `MANIFEST.json`).
- `scripts/tests/test_pg_doc_templates_common.py` (unit tests com mock HTTP).
- `scripts/pg_extract_doc_template_assets.py` (extração de anexos para `assets_extracted/*.md` e `*.txt`).
- integração de hashes/metadados em `doc_templates/MANIFEST.json`.

`Validacao factual ja executada`:
- parse/execução dos novos scripts sem erros locais.
- unit tests do helper Python a passar.
- `dry-run` do pull concluido com sucesso.
- pull real concluido com sucesso para `doc_templates/`.
- `TPL_PONTO_SITUACAO` validado em `MANIFEST.json` com anexos e artefactos extraidos.

`Fecho operacional`:
- gates A+B+C+D executados e marcados em `docs/PG_004_OPERATIONAL_CLOSURE_CHECKLIST.md`.
- validação operacional confirmada em 2026-05-27 (bootstrap assistido e materialização factual dos templates no Odoo Knowledge + repo).

`Racional`:
A intenção e coerente, mas o modelo atual depende de templates locais legíveis diretamente pelos agentes. Se a migração eliminar a materialização local, perde-se auditabilidade, previsibilidade e uso offline.

`Dependencias`:
- `BLK-000`
- definição da estrategia de publicação e materialização local

`Impacto tecnico`:
Integração API com Odoo externo, modelo de autenticação, sincronização e export de templates para o repo ou `.pg_framework`, revisão das instruções dos agentes e dos scripts de sync de assets.

`Criterios de aceitacao`:
- o Odoo Knowledge passa a ser a origem editorial oficial dos templates
- os templates continuam disponíveis localmente para consumo pelos agentes
- existe regra clara de versão, publicação e fallback quando a API não estiver disponível
- `doc_templates` deixa de ser gerido manualmente como source of truth no `_pg_template`

### PG-005 - Suportar múltiplos projetos no mesmo repo e branch

`ID`: `PG-005`

`Objetivo`:
Suportar onboarding e operação de múltiplos projetos no mesmo repo e branch, para cenários multiempresa ou multi-projeto.

`Decisao`:
`ADIAR`

`Estado`:
`ADIADO (CONTRATO APROVADO EM 2026-05-27; AGUARDA REPO PILOTO + CONFIRMACAO ESFORCO F1)`

`Discovery arquitetural`:
Fechado em 2026-05-27. Contrato completo em `docs/PG_005_ARCHITECTURE_CONTRACT.md`. Decisões arquitecturais fechadas: namespacing hierarquico sob `.pg/projects/{project_key}/`; registo central em `.pg/PG_PROJECT_INDEX.json`; `PG_CONTEXT.md` por projeto em `projects/{key}/PG_CONTEXT.md`; `PG_CONTEXT.md` raiz = indice curto em modo multi; tokens schema actual + campo `project_key` opcional; limite operacional 20 projetos/repo sem hard limit em F1.

`Spec pg_brodoo`:
Fechado em 2026-05-27. Spec completa em `docs/PG_005_BRODOO_CHANGE_SPEC.md`. Ficheiros a tocar: 14 (campo + publisher refactor + 9 serviços + view + testes + migração). Padrão central: `_build_publisher(project)` em cada serviço; `_path(artifact_key)` no publisher; `update_project_index` após publish bem-sucedido.

`Racional`:
O modelo atual assume `1 projeto -> 1 repo/branch` e publica paths globais fixos. Sem namespacing, os snapshots colidem e o `PG_CONTEXT.md` deixa de ser semanticamente seguro.

`Dependencias`:
- `BLK-000`
- decisão arquitetural explicita sobre tenancy lógica do espelho

`Impacto tecnico`:
Redesign do publisher, dos paths `.pg`, do `PG_CONTEXT.md`, do onboarding, das constraints de projeto e da compatibilidade com projetos já existentes. O impacto esperado em testes, migração e operação e alto.

`Criterios de aceitacao`:
- existe estrategia de namespacing por projeto sem colisão de artefactos
- o contexto gerado distingue claramente cada projeto partilhando o mesmo repo e branch
- a solução preserva compatibilidade ou define migração formal para projetos atuais
- o item só entra em implementação depois de existir contrato arquitetural aprovado

### PG-006 - Script de checkout automático para branch Brodoo antes de sessão de briefing

`ID`: `PG-006`

`Objetivo`:
Criar script que, antes de abrir uma sessão de briefing com agente AI num repositório de cliente, faça automaticamente checkout do branch correcto onde o Brodoo publica os artefactos `.pg/`, evitando que o agente leia dados desactualizados do branch de produção (código).

`Decisao`:
`ACEITAR`

`Estado`:
`FECHADO (SCRIPT EM PRODUCAO; PASSO 1 DO RITUAL OBRIGATORIO)`

`Implementacao`:
`scripts/pg_checkout_brodoo_branch.ps1` existe e está em produção. O `templates/AGENTS_SHARED.md` fixa-o como **passo 1** do ritual obrigatório de arranque de cada chat, e como pré-condição de todos os outros passos: se o checkout para a branch Brodoo falhar, o agente pára e reporta. O standard da branch Brodoo passou entretanto a ser `brodoo` (nunca `main`, que é produção do cliente).

`Racional`:
Alguns repos têm o branch de produção Odoo.sh (`main`) separado do branch onde o Brodoo publica o espelho (ex: `teste` no jmmgroup, `Teste` no domusacropoles, `Test` no Essani/MIMO/GBN). Se o agente abrir numa sessão no branch de produção, vai ler os artefactos `.pg/` antigos (estrutura legada) em vez dos actuais (estrutura multi-projecto namespaced). Isto causa respostas factualmente erradas — por exemplo, reportar a última mensagem do cliente como sendo de semanas atrás quando há mensagens de hoje.

O problema foi observado em produção na sessão do jmmgroup em 2026-06-03: o agente respondeu que a última mensagem era de 28/05 quando havia uma mensagem do cliente de hoje às 08:44, porque estava no branch `main` e a ler o path legado `.pg/chatter/chatter.json`.

`Dependencias`:
- Mapeamento estável dos branches Brodoo por repo (derivável de `.pg/PG_PROJECT_INDEX.json` ou do campo `repository_branch` em `project.json`)
- Conhecimento da lista de repos locais e respectivos paths

`Impacto tecnico`:
Novo script PowerShell (ex: `pg_checkout_brodoo_branch.ps1`) que:
1. lê o `project.json` ou `PG_PROJECT_INDEX.json` do repo para obter `repository_branch`
2. faz `git fetch origin` e `git checkout <branch>`
3. confirma que `.pg/projects/<key>/` existe após o checkout
4. aceita um repo específico ou itera sobre todos os repos configurados

Opcionalmente: integrar no ritual de arranque do `AGENTS_SHARED.md` como passo 1.5 (antes do `git pull`).

`Criterios de aceitacao`:
- o script aceita path de repo como argumento ou opera sobre lista configurada
- detecta automaticamente o branch Brodoo correcto sem intervenção manual
- confirma após checkout que os artefactos `.pg/projects/` estão presentes
- emite aviso claro se o branch Brodoo não existir no remote
- documentado em `BRODOO_GUIA_OPERACIONAL.md` como passo obrigatório pré-briefing

### PG-007 - Corrigir a origem do inventário de módulos no espelho `odoo_env.json`

`ID`: `PG-007`

`Objetivo`:
Garantir que o `odoo_env.json` (marco M1 do espelho) contém o inventário de módulos do **Odoo do cliente**, identificando sempre qual base foi inventariada e quando, e declarando a ausência de inventário como estado explícito em vez de a confundir com "nada instalado".

`Decisao`:
`ACEITAR F1` / `ABERTO F2`

`Estado`:
`EM CURSO (F1 IMPLEMENTADO EM 2026-08-11; AGUARDA DEPLOY + REPUBLICACAO DOS ESPELHOS; D1/D2 EM ABERTO PARA F2)`

`F1 implementado`:
2026-08-11. Schema `1.1` com bloco `collection`; `_installed_modules()` removido do payload builder; validação do estado; `collected_at` fora do `payload_hash`; `AGENTS_SHARED` com a regra de leitura do `status`; preflight a validar estado em vez de presença. Suite do addon comparada com baseline em worktree isolado, sem regressão. Falta o **deploy do addon no Odoo PG** e a **republicação dos 13 espelhos** — até lá o publisher em produção continua a emitir o payload antigo, mas o preflight já sinaliza esses espelhos como origem desconhecida.

`Discovery arquitetural`:
Fechado em 2026-08-10. Contrato completo em `docs/PG_007_ODOO_ENV_COLLECTION_CONTRACT.md`. Proposta: separar recolha (lado do operador, canal `production`), persistência (modelo novo no Odoo PG, por ligação) e publicação (publisher actual, que continua o único escritor). Oito decisões enunciadas, três bloqueantes: D1 propriedade do ficheiro, D2 granularidade do inventário, D3 declaração de ausência e de origem.

`Racional`:
`_installed_modules()` (`pg_brodoo/services/project_mirror_payload_builder.py:697-700`) inventaria `self.env`, que é a base onde o addon corre — o Odoo da Parâmetro Global — e não a base do cliente. Verificado em 2026-08-10 nos 13 espelhos publicados: 483–488 módulos declarados, 100% dos nomes coincidentes com os módulos instalados no Odoo da Parâmetro Global, incluindo `pg_brodoo`, `pg_doc_templates` e `pg_project_budget_import`. O comportamento está consagrado em teste (`tests/test_m1m3_env_deliverables.py:27` afirma `assertIn('pg_brodoo', names)`).

O `odoo_env.json` é a fonte de verdade nº 6 do `AGENTS_SHARED.md` e o árbitro do passo 1 (standard já instalado) contra o passo 2 (standard adicional) da ordem obrigatória de decisão. Com o inventário da Parâmetro Global no lugar do inventário do cliente, o agente conclui que quase tudo já está instalado e recomenda como "já disponível" o que exige instalar um módulo — o erro que a ordem obrigatória existe para evitar.

Acresce que a documentação da framework se contradiz: `docs/PG_ODOO_CLIENT_CHANNELS_TEMPLATE_MAP.md:29,38-40` já estabelece que os módulos instalados vêm do canal `production`, enquanto o `AGENTS_SHARED.md` aponta o espelho como fonte primária.

`Dependencias`:
- nenhuma bloqueante; independente de `PG-005`, mas o schema respeita os paths namespaced já em produção
- F2 depende do fecho de D1 e D2; F1 depende apenas de D3

`Impacto tecnico`:
F1 (contrato e estado explícito): `ODOO_ENV_SCHEMA_VERSION` de `1.0` para `1.1` com bloco `collection` (`status`, `purpose`, `base_url`, `database`, `collected_at`, `collected_by`, `unavailable_reason`); publisher deixa de publicar o inventário local e emite `unavailable`; `AGENTS_SHARED.md` reescreve a fonte de verdade nº 6; `pg_preflight_context.ps1` valida estado em vez de presença; teste do M1 invertido; republicação dos 13 espelhos.

F2 (recolha e persistência): modelo `pg.odoo.env.snapshot` por ligação; script `pg_collect_odoo_env.ps1`; `_installed_modules()` passa a ler o snapshot.

`Criterios de aceitacao`:
- nenhum `odoo_env.json` da frota contém módulos da base da Parâmetro Global
- o artefacto identifica sempre a base inventariada e o momento da recolha
- ausência de inventário é distinguível de ausência de módulos instalados
- o preflight avisa quando o inventário está ausente, obsoleto ou de origem desconhecida (schema `1.0`)
- `payload_hash` estável entre builds consecutivos sem recolha nova (regressão AUD-04)
- um cliente on-premise em rede privada é coberto pelo fluxo de recolha

### PG-008 - Permissões em modo automático: alertar em vez de bloquear

`ID`: `PG-008`

`Objetivo`:
Fazer com que o modo automático permita as operações de que o trabalho real depende, e que o agente **alerte** quando uma ação é arriscada ou pressupõe conhecimento e autorização do utilizador — em vez de a bloquear e obrigar a sair do modo automático.

`Decisao`:
`ACEITAR` (pedido de Bruno Pinheiro, 2026-09-11)

`Estado`:
`POR IMPLEMENTAR`

`Racional`:
O gate de permissão atual falha nos dois sentidos ao mesmo tempo.

**Bloqueia o que devia deixar passar.** `FACTO OBSERVADO` (2026-09-11): o classificador do modo automático recusou o `-Apply` do `pg_align_fleet_framework.ps1` duas vezes e a escrita `active: false` num registo de catálogo do Odoo da Parâmetro Global. Nenhuma das três tinha alternativa: a propagação da framework à frota **é** um `-Apply`, e arquivar um registo **é** um `write`. O trabalho parou até o utilizador sair do modo automático manualmente.

**E não protege quando devia.** Quem trabalha em modo manual recebe um pedido de confirmação por cada ação, muitas delas triviais. O resultado previsível é responder «sim» a tudo por hábito — e nesse ponto a confirmação deixou de ser uma decisão e passou a ser um ruído que se despacha. Um gate que se responde sem ler não protege de nada; dá apenas a aparência de proteção, que é pior do que não ter gate, porque desloca a responsabilidade para quem carregou no botão.

Acresce o efeito de escala: sair do modo automático levanta o gate para **tudo** o que se segue, não só para a ação que o motivou. A granularidade do remédio é pior do que a do problema.

O critério certo não é *quem carrega no botão*, é *o agente explicar o que vai fazer e porquê antes de o fazer*, e parar sozinho quando o risco o justifica. Isso é exatamente o que o resto deste contrato já exige em `Gestão de incerteza e evidência` e em `Antes de alterar o que já funciona`: declarar factos, classificar, dimensionar. A diferença é que essas regras vinculam o **raciocínio** do agente, e o gate de permissão vincula a **mecânica** — e as duas não estão alinhadas.

`Dependencias`:
- configuração de permissões do Claude Code (`.claude/settings.json`, regras de `Bash` e de ferramentas) — é aí que a lista de operações permitidas se declara
- articulação com a regra de escrita em produção de clientes, que **não** deve ser relaxada: o `pg_odoo_migration_guard.py` continua a ser o ponto único de passagem, com `--confirm` e `--allow-prod`

`Impacto tecnico`:
- declarar em `.claude/settings.json` as operações rotineiras da framework que hoje são bloqueadas (`-Apply` do alinhador, `write` no Odoo da Parâmetro Global pelo canal Brodoo, `push` para branches Brodoo)
- definir a fronteira do que **continua** a exigir autorização explícita por sessão: escrita em produção de clientes, eliminação de dados, `push --force`, qualquer operação sobre `vendor/odoo_src`
- documentar em `AGENTS_SHARED.md` a obrigação correspondente do lado do agente: antes de uma ação desta classe, dizer em texto o que vai fazer, sobre que registo, e o que é reversível — e parar quando a resposta a «isto é o que o utilizador quer?» não estiver no pedido

`Criterios de aceitacao`:
- a propagação da framework à frota corre em modo automático, de uma ponta à outra, sem intervenção
- uma escrita em produção de um cliente **continua** a parar e a pedir autorização, mesmo em modo automático
- antes de cada ação da classe permitida, o agente declara em texto o alvo e a reversibilidade, e essa declaração é verificável na transcrição
- nenhum passo do ritual obrigatório exige sair do modo automático

`Nota de perímetro`:
Este item é sobre a configuração do ambiente de trabalho dos agentes, não sobre o método consultivo. Fica aqui por ser onde o backlog operativo da framework vive, e por o sintoma ter aparecido a executar trabalho da framework.

### PG-009 - Propagar a proibição do Studio ao publisher e aos entregáveis

`ID`: `PG-009`

`Objetivo`:
Alinhar com a proibição do Odoo Studio (v2.29.0) os dois sistemas que ficaram fora do alcance dessa release: o addon `pg_brodoo`, que vive noutro repositório, e os templates documentais que vão para o cliente.

`Decisao`:
`ACEITAR` (Bruno Pinheiro, 2026-09-11) — a executar quando houver disponibilidade

`Estado`:
`EXECUTADO EM 2026-09-11, A AGUARDAR MERGE E REPUBLICACAO`

Executado no mesmo dia, a pedido de Bruno Pinheiro:
- **addon**: branch `feat/studio-proibido` em `parametro-odoo/Parametro_Global` (commit `a7b3a4a`), publicada e **a aguardar PR e revisão**. Campo novo `pg_studio_applied`; `pg_studio_allowed` deprecado e fora das vistas, **não apagado**. O `PG_CONTEXT.md` gerado deixa de anunciar a permissão e passa a declarar se já existe Studio; o wizard deixa de bloquear pela permissão e passa a pedir o facto; ambos os payloads publicam os dois campos
- a decisão entre reaproveitar o campo e criar um novo foi **dimensionada contra a produção**, como manda a regra «Antes de alterar o que já funciona»: 49 projetos declaram `yes` e 2 declaram `no`. Reaproveitar inverteria o significado desses 51 registos — daí o campo novo
- **`TPL_ORCAMENTO`**: editado no Knowledge (artigo 739), verificado por releitura, e o `pg_pull_doc_templates.ps1` trouxe a alteração para o repositório. A ordem anunciada ao cliente passou a três passos

Falta:
- **PR, revisão e merge** do `feat/studio-proibido`. A suite do addon exige instância Odoo e **não foi corrida**; validou-se que os 7 módulos Python compilam e os 2 XML são bem formados
- **republicação dos espelhos** depois do merge, para a linha antiga sair dos `PG_CONTEXT.md` da frota
- avisar **Pedro Coelho**, autor e mantenedor do artigo 739 do Knowledge
- `TPL_PLANEAMENTO_ONBOARDING_PROJETO` (linhas 23 e 63), que lista `studio_allowed` entre os campos do onboarding: acompanha o merge do addon

`Racional`:
A v2.29.0 tirou o Studio da ordem de decisão, do contrato, do template de `PG_CONTEXT.md` e dos quatro prompts de apoio. Ficaram dois sistemas a dizer o contrário, e ambos são visíveis a quem não lê o contrato:

- o **publisher** escreve nos `PG_CONTEXT.md` de toda a frota uma linha `- Odoo Studio: <permissão>`, como se fosse uma opção disponível sujeita a autorização contratual;
- o **wizard de onboarding** exige clarificar se o Studio é permitido antes de deixar avançar. Passou a ser um gate sobre uma pergunta que já não informa decisão nenhuma;
- o **`TPL_ORCAMENTO`** anuncia ao cliente, num orçamento, a ordem de decisão em quatro passos com o Studio no terceiro. É a nossa metodologia declarada por escrito a um cliente, e está desactualizada.

Deixar assim reintroduz o Studio pela porta do lado: quem ler um `PG_CONTEXT.md` gerado, ou abrir o wizard, conclui que o Studio é uma opção cuja permissão se negoceia.

`Dependencias`:
- o addon vive em **`parametro-odoo/Parametro_Global`**. A pasta `pg_brodoo/` do `_pg_template` é **espelho de teste**, e editá-la cria um fork silencioso — ver [[project_pg_brodoo_source_of_truth]]. A alteração é feita lá, com a suite do addon a correr, e só depois o espelho acompanha
- implica migração de dados: o campo `pg_studio_allowed` tem valores em produção nos projetos existentes
- republicação dos espelhos para a linha desaparecer dos `PG_CONTEXT.md` da frota

`Impacto tecnico`:

**`pg_brodoo` (decisão de desenho a tomar primeiro).** O campo `pg_studio_allowed` responde hoje à pergunta *«o cliente autoriza Studio?»*, que deixou de nos interessar — não usamos Studio independentemente da resposta. A pergunta útil passou a ser *«existe Studio **já aplicado** neste ambiente?»*, porque isso muda o comportamento do sistema e não se vê no código. Duas opções:
- **(a) reaproveitar** o campo, mudando o rótulo e o significado — preserva os dados, mas um valor `yes` antigo significa «autorizado» e passaria a ler-se «existe», o que é falso e pior do que não ter dado;
- **(b) campo novo** `pg_studio_applied` e o antigo depreciado (não apagado, pela mesma regra de nunca destruir camadas anteriores). **Recomendado**, por (a) inverter silenciosamente o significado de dados históricos.

Pontos a tocar no addon: `models/project_project.py` (definição do campo e as duas listas de campos publicados, linhas ~254, ~642, ~676), `services/project_mirror_context_builder.py:173` (a linha escrita no `PG_CONTEXT.md`), `services/project_mirror_payload_builder.py:291` e `services/project_scope_payload_builder.py:361` (payloads), `wizards/pg_ai_onboarding_wizard.py` (campo, validação bloqueante ~174-175, defaults e escrita ~428) e os testes `tests/common.py` e `tests/test_onboarding_wizard.py`.

**Templates documentais.** `TPL_ORCAMENTO.md:40` — remover o Studio da ordem apresentada ao cliente, deixando três passos. `TPL_PLANEAMENTO_ONBOARDING_PROJETO.md:23,63` — acompanha a decisão do campo no addon. Estes templates são geridos na App Knowledge da Parâmetro Global e sincronizados pelo ritual, pelo que a edição é **no Knowledge**, não no ficheiro sincronizado.

**Verificado e sem alteração necessária:** o `TPL_MIGRACAO_DADOS_ODOO.md` menciona Studio cinco vezes, e as cinco estão **correctas** — tratam de migrar Studio → standard e da regra de nunca apagar a camada anterior, que é exactamente o que continua permitido. Os `doc_templates/assets_extracted/` são extrações de referência visual, não instruções.

`Criterios de aceitacao`:
- nenhum `PG_CONTEXT.md` gerado pelo publisher apresenta o Studio como permissão contratual
- o wizard de onboarding não bloqueia por falta de resposta sobre permissão de Studio
- o valor histórico de `pg_studio_allowed` não é reinterpretado com outro significado
- nenhum entregável ao cliente anuncia uma ordem de decisão com o Studio
- a suite do addon passa, e os espelhos da frota são republicados
- o `TPL_MIGRACAO_DADOS_ODOO` mantém intactas as regras de migração do Studio existente

### PG-010 - Suportar patch a produção viva e trabalho fora de repositórios

`ID`: `PG-010`

`Objetivo`:
Cobrir de facto os modos de trabalho que a framework hoje finge cobrir: desenvolvimento por patch a um Odoo vivo, e trabalho em pastas que não são repositórios.

`Decisao`:
`ACEITAR` — decisão de perImetro de Bruno Pinheiro, 2026-09-11: **a framework deve suportar estes modos**, e não declarar que não os cobre.

`Estado`:
`POR IMPLEMENTAR` (várias fases; nenhuma bloqueia as outras)

`Racional`:
A auditoria do givachoice deixou esta pergunta expressamente em aberto: a framework devia **suportar** estes modos, ou **declarar** que não os cobre, como já faz para os projetos não-Odoo? O que não podia continuar era a terceira hipótese, que era a de então: fingir que os cobre.

Decidido **suportar**. E a consequência imediata é que o trabalho **não é inventar**: o givachoice já construiu os mecanismos, sozinho, e eles funcionam. O que falhou foi não voltarem para a framework — «nada disso é reaproveitável por outro projeto, e nada disso volta». Suportar significa sobretudo **promover o que existe**, com os caminhos parametrizados.

Inventário do que há para promover (`auditoria_v19/`, verificado a 2026-09-11):

- **`espelhar_addons_servidor.sh`** — a peça central. Publica em branches `live/*` o que está **realmente** instalado nos servidores. Bem desenhado e generalizável: espelha as árvores de addons e, do core, **só o desvio** (o core inteiro passa de 1 GB e não compensa — compensa saber que alguém lhe tocou e ver o quê); escolhe sozinho o método de deteção (`git status` se a pasta for repositório, data de modificação contra carimbo se não for); mantém o `.git` fora das pastas espelhadas; e **não escreve sem `CONFIRMA=1`**. Só os caminhos são específicos.
- **`exportar_objectos_bd.sh`** — alimenta `live/objectos-bd`, com os objectos da base de produção e de testes.
- **o padrão de janela de manutenção** — guião antes, registo durante, `REVERTER_*.json` para desfazer. Existe em várias instâncias datadas e nunca foi formalizado como método.
- **a pasta `deploys/`** com o registo do que foi implantado e como se reverte.

`Dependencias`:
- a regra de implantação de código (v2.31.0) já existe e é o contrato que estas ferramentas passam a cumprir
- o reconhecimento do espelho como fonte (v2.30.0) já existe; falta o **mecanismo** que o produz
- o `pg_init_work_folder.ps1` (v2.27.0) já declara factos numa pasta; falta o resto do ritual funcionar lá

`Impacto tecnico`, por fases independentes:

**F1 — o espelho do código vivo, generalizado.** Promover o `espelhar_addons_servidor.sh` a script da framework, com os caminhos, as branches e o remoto vindos de parâmetros ou de um ficheiro de configuração por projeto. É a fase de maior retorno: resolve, para qualquer projeto que faça patch a produção viva, o problema de o repositório não ser o código que corre. Já há verificador do lado de cá (`pg_compare_client_addons.py --ref`).

**F2 — a janela de manutenção como método.** Template documental (guião, registo, reversão) e estrutura de pastas, a partir das instâncias reais do givachoice. É o que dá forma aos passos 2, 3 e 5 da regra de implantação.

**F3 — objectos da base de dados.** Promover o `exportar_objectos_bd.sh`. Permite ver em diff o que mudou na configuração de um Odoo vivo — incluindo o que o Studio lá deixou.

**F4 — o ritual em pastas que não são repositórios.** Hoje o `pg_init_work_folder` declara os factos e o preflight lê-os, mas o **registo de consumo de tokens não acontece** nessas pastas (o hook depende de `.pg/`), pelo que o trabalho feito ali continua invisível à medição — que foi precisamente o que obrigou a auditoria a pedir extrações máquina a máquina.

`Criterios de aceitacao`:
- um projeto novo que faça patch a produção viva consegue montar o espelho do código com um comando da framework, sem copiar guiões de outro projeto
- o `pg_compare_client_addons.py --ref` confirma o espelho desse projeto
- uma janela de manutenção tem guião, registo e reversão por template, e não por improviso
- o trabalho feito numa pasta declarada aparece no registo de consumo
- nada disto obriga um projeto normal a mudar o que faz: como no `PROJECT_PROFILE.json`, é por adesão e não por imposição

`Nota de método`:
Não abstrair antes de ter o segundo caso. O GBUK também implanta código num servidor de cliente, mas prova-o de outra maneira (impressão digital SHA-256 pedida ao módulo, em vez de espelho). A F1 deve nascer parametrizada a partir do givachoice, e só quando o GBUK a usar é que se extrai o que for comum aos dois — como ficou combinado no `PG-009`.

## Resumo de filtro

- `Aceitar`: `BLK-000`, `PG-001`, `PG-006`, `PG-007` (F1)
- `Reformular`: `PG-002`, `PG-004`
- `Adiar`: `PG-005`, `PG-007` (F2, até fecho de D1 e D2)
