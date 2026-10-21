# PG_005_ARCHITECTURE_CONTRACT

## Metadados

| Campo | Valor |
|---|---|
| Item de backlog | `PG-005` |
| Tipo de documento | Contrato arquitetural (discovery; sem implementação) |
| Estado | `DECISÕES FECHADAS — AGUARDA REPO PILOTO + CONFIRMAÇÃO DE ESFORÇO F1` |
| Autor | Claude Code (Sonnet 4.6) — sessão discovery 2026-05-27 |
| Decisões fechadas em | 2026-05-27 (Pedro Coelho) |
| Dependências validadas | `BLK-000`, `PG-001`, `PG-002`, `PG-003`, `PG-004` todos `FECHADOS` |
| Próximo passo | Identificar repo piloto + confirmar disponibilidade F1 → abrir implementação |

---

## 1. Objetivo e enquadramento

O objetivo do PG-005 é suportar onboarding e operação de **múltiplos projetos no mesmo repo e branch**, para cenários multi-empresa ou multi-projeto, sem colisão de artefactos e com contexto semanticamente seguro para agentes AI.

O modelo atual assume `1 projeto → 1 repo/branch` com paths globais fixos:

```
.pg/PG_SCOPE_SYNC.json
.pg/PG_PROJECT_STATUS_SYNC.json
.pg/PG_DECISIONS_SYNC.json
...
PG_CONTEXT.md                  (raiz)
PG_SCOPE_INTAKE.yaml           (raiz)
```

Sem namespacing, um segundo projeto sobrescreve silenciosamente os snapshots do primeiro. `PG_CONTEXT.md` deixa de ser semanticamente seguro porque mistura informação de projetos distintos.

**Restrições do contrato:**
- Não quebrar operação atual single-project por defeito.
- Não implementar código nesta fase.
- Preservar auditabilidade e previsibilidade dos artefactos para agentes AI.

---

## 2. Análise do estado actual

### 2.1 Factos observados

`FACTO OBSERVADO`: O bootstrap (`pg_bootstrap_repo.ps1`) cria `.pg/` com todos os JSONs como paths globais fixos. Não existe registo de projeto nem namespacing.

`FACTO OBSERVADO`: O contrato de validação (`pg_scope_sync_common.ps1`) usa `project_id` como campo obrigatório nos JSONs mas não o usa para derivar paths. O campo existe mas não tem função de routing.

`FACTO OBSERVADO`: `pg_build_pg_context.ps1` lê `PG_SCOPE_INTAKE.yaml` da raiz e escreve `PG_CONTEXT.md` na raiz. Caminho hardcoded.

`FACTO OBSERVADO`: `pg_smoke_test_repo.ps1` valida paths hardcoded: `.pg/PG_SCOPE_SYNC.json`, etc. Não itera projetos.

`FACTO OBSERVADO`: `PG_CONTEXT.md` usa marcadores `<!-- PG_AUTO:MARKER:START/END -->` substituídos por scripts. Existe apenas uma instância na raiz.

`FACTO OBSERVADO`: O campo `project_id` em `PG_SCOPE_SYNC.json` é obrigatório (`Assert-RequiredValueProperty`) e pode ser inteiro ou string.

### 2.2 Inferências

`INFERÊNCIA`: Em cenário multi-projeto, a ausência de namespacing causa colisão silenciosa — o último publisher a escrever vence.

`INFERÊNCIA`: Agentes AI a ler `PG_CONTEXT.md` num repo multi-projeto sem namespacing recebem contexto ambíguo ou errado, com risco elevado de alucinação factual.

`INFERÊNCIA`: A introdução de `-ProjectKey` como parâmetro opcional nos scripts existentes é a mudança de menor impacto, pois preserva todos os call sites existentes.

### 2.3 Pontos por validar

`PONTO POR VALIDAR`: Quantos projetos simultâneos no mesmo repo são o caso de uso real alvo? 2? 10? A resposta afeta a decisão de formato do `PG_CONTEXT.md` (índice vs. secções vs. ficheiros por projeto).

`PONTO POR VALIDAR`: O cenário multi-projeto implica Odoos diferentes (versões, instâncias) por projeto, ou os projetos partilham o mesmo Odoo mas têm projetos distintos dentro?

`PONTO POR VALIDAR`: O contrato de `vendor/odoo_src` e `.pg_framework` continua a ser partilhado (1 por repo) mesmo em multi-projeto? Assumido que sim, mas deve ser confirmado.

---

## 3. Proposta principal recomendada — Opção A: Namespacing hierárquico sob `.pg/projects/{project_key}/`

### 3.1 Decisão recomendada

**Adoptar namespacing hierárquico com sub-directórios por projecto sob `.pg/projects/`**, com registo central em `.pg/PG_PROJECT_INDEX.json` e `PG_CONTEXT.md` por projeto em `projects/{key}/PG_CONTEXT.md`.

Modo legacy (single-project sem `PG_PROJECT_INDEX.json`) continua a funcionar sem alteração.

### 3.2 Estrutura de paths alvo

```
.pg/
  PG_PROJECT_INDEX.json                    # registo global dos projetos (schema v2+)
  projects/
    {project_key}/                         # 1 pasta por projeto ativo
      PG_SCOPE_SYNC.json
      PG_PROJECT_STATUS_SYNC.json
      PG_DECISIONS_SYNC.json
      PG_RISKS_SYNC.json
      PG_DELIVERIES_SYNC.json
      PG_REQUIREMENTS_SYNC.json
      PG_PROJECT_PLAN_SYNC.json
      PG_BUDGET_SYNC.json
      PG_EFFORT_SYNC.json
      tokens/
        consumption.jsonl
  tokens/                                  # legacy / nível repo (preservado)
    consumption.jsonl

projects/                                  # contextos por projeto (nivel raiz repo)
  {project_key}/
    PG_CONTEXT.md                          # contexto AI do projeto
    PG_SCOPE_INTAKE.yaml                   # intake do projeto

PG_CONTEXT.md                             # legacy — single-project OU índice global
```

> **Nota sobre `projects/` na raiz**: esta pasta é ao nível do repositório, não dentro de `.pg/`. Separa os artefactos operacionais (JSON em `.pg/`) dos artefactos de contexto AI (Markdown em `projects/`). Simplifica o `.gitignore` e evita misturar JSONs com Markdown no mesmo nível.

### 3.3 Regra de identificação estável por projeto (`project_key`)

O `project_key` é o identificador estável e imutável de cada projeto no repo. Regras de derivação:

1. **Derivado de `project_name`** da instância Odoo, normalizado para slug:
   - lowercase
   - substituir espaços e caracteres não-alfanuméricos por `-`
   - colapsar múltiplos `-` consecutivos
   - máximo 48 caracteres
   - exemplo: `"Alpha CRM - Fase 2"` → `alpha-crm-fase-2`

2. **Registado em `PG_PROJECT_INDEX.json`** com o `project_id` Odoo, para garantir unicidade mesmo que o nome mude:
   ```json
   {
     "schema_version": "2.0",
     "registry": [
       {
         "project_key": "alpha-crm",
         "project_id": 42,
         "project_name": "Alpha CRM",
         "odoo_source": "https://odoo.example.com",
         "registered_at": "2026-05-27T10:00:00Z",
         "status": "active"
       }
     ]
   }
   ```

3. **Imutável após registo**: se o nome do projeto mudar no Odoo, o `project_key` não muda. Adicionar `display_name` ao registry se necessário.

4. **Prevenção de colisões**: antes de registar um novo projeto, o script de bootstrap valida que o `project_key` derivado não está já em uso por outro `project_id`. Se houver colisão, acrescenta sufixo numérico: `alpha-crm-2`.

### 3.4 Regras de identificação do modo (legacy vs. multi)

| Condição | Modo | Comportamento |
|---|---|---|
| `.pg/PG_PROJECT_INDEX.json` **não existe** | `legacy` | paths actuais sem namespace; compatibilidade total |
| `.pg/PG_PROJECT_INDEX.json` **existe** com `schema_version: "2.0"` | `multi` | paths com namespace; `-ProjectKey` obrigatório nos scripts |
| `.pg/PG_PROJECT_INDEX.json` existe mas `registry` tem 1 entrada | `multi-single` | paths com namespace; `-ProjectKey` pode ser omitido (único) |

### 3.5 `PG_CONTEXT.md` multi-projeto

**Formato alvo**: um `PG_CONTEXT.md` por projeto, em `projects/{project_key}/PG_CONTEXT.md`.

Na raiz, `PG_CONTEXT.md` passa a ser um **índice global** com links e resumo de cada projeto:

```markdown
# PG_CONTEXT - Índice Global

## Projetos ativos

| Projeto | Key | Contexto | Último sync |
|---|---|---|---|
| Alpha CRM | `alpha-crm` | [PG_CONTEXT](projects/alpha-crm/PG_CONTEXT.md) | 2026-05-27 |
| Beta ERP  | `beta-erp`  | [PG_CONTEXT](projects/beta-erp/PG_CONTEXT.md)  | 2026-05-20 |

## Nota para agentes AI

Em modo multi-projeto, este ficheiro é apenas um índice.
Antes de qualquer análise, identificar o projeto alvo e ler o seu PG_CONTEXT.md específico.
```

**Regras de leitura por agentes:**

1. Agente inicia sessão → lê `PG_CONTEXT.md` na raiz.
2. Se raiz tiver índice (sinal: linha `## Projetos ativos`) → identificar projeto alvo via contexto da sessão ou perguntar ao utilizador.
3. Carregar `projects/{project_key}/PG_CONTEXT.md` como contexto operativo.
4. Em single-project legacy: `PG_CONTEXT.md` na raiz continua a ser o contexto operativo.

**Compatibilidade com consumo actual:**

- `AGENTS_SHARED.md` adiciona instrução: "Se `PG_CONTEXT.md` na raiz for um índice global, identificar e carregar o contexto do projeto alvo em `projects/{key}/PG_CONTEXT.md`."
- Scripts como `pg_apply_project_status_sync.ps1` recebem parâmetro `-ProjectKey` e resolvem `projects/{key}/PG_CONTEXT.md` ou fallback para raiz em legacy.

### 3.6 Marcadores `PG_AUTO` em contexto multi-projeto

Os marcadores existentes (`<!-- PG_AUTO:IDENTIFICACAO:START -->` etc.) continuam a funcionar dentro de cada `projects/{key}/PG_CONTEXT.md`. Não há alteração ao formato interno do ficheiro por projeto.

### 3.7 Publisher/sync em multi-projeto

**Princípio**: scripts existentes recebem `-ProjectKey` como parâmetro opcional. Quando presente, resolvem paths para `.pg/projects/{project_key}/`. Quando ausente, comportam-se como hoje (modo legacy).

**Resolução de path (função comum a extrair em `pg_project_path_common.ps1`):**

```powershell
function Resolve-PgProjectPath {
  param(
    [string]$RepoPath,
    [string]$ProjectKey,     # se vazio: modo legacy
    [string]$ArtifactName   # ex: "PG_SCOPE_SYNC.json"
  )

  if ([string]::IsNullOrWhiteSpace($ProjectKey)) {
    return Join-Path $RepoPath ".pg\$ArtifactName"
  }

  return Join-Path $RepoPath ".pg\projects\$ProjectKey\$ArtifactName"
}
```

**Scripts a atualizar (F1):**
- `pg_bootstrap_repo.ps1` — criar estrutura `/projects/{key}/` e registar em `PG_PROJECT_INDEX.json`
- `pg_build_pg_context.ps1` — ler `projects/{key}/PG_SCOPE_INTAKE.yaml`, escrever `projects/{key}/PG_CONTEXT.md`
- `pg_apply_project_status_sync.ps1` — `-ProjectKey` opcional
- `pg_apply_scope_sync.ps1` — `-ProjectKey` opcional
- `pg_refresh_pg_context.ps1` — iterar projetos se multi-mode
- `pg_smoke_test_repo.ps1` — iterar projetos registados

**Scripts a atualizar (F2):**
- Todos os restantes `pg_validate_*.ps1`, `pg_log_token_consumption.ps1`, etc.

### 3.8 Estratégia de locks, atomicidade e consistência

**Regra por artefacto**: cada snapshot JSON é escrito atomicamente (write to temp → rename), seguindo o mesmo padrão já adoptado em `pg_pull_doc_templates.ps1` (staging + promote).

**Regra de isolamento entre projetos**: paths distintos garantem isolamento. Não é necessário lock entre projetos diferentes — são ficheiros disjuntos.

**Regra de lock intra-projecto**: em cenários de automação (GitHub Actions), um único workflow por projeto é suficiente. Não há concorrência intra-projecto porque o trigger é o commit no snapshot.

**Comportamento em falha parcial**: se o sync de um projeto falha, os outros não são afetados. `pg_smoke_test_repo.ps1` reporta o estado de cada projeto independentemente.

**Consistência do `PG_PROJECT_INDEX.json`**: operação de registo (add/remove) deve ser atómica. Script de registo usa read → validate → write. Não é necessário lock de ficheiro (operação manual, não concorrente).

---

## 4. Alternativas rejeitadas

### 4.1 Opção B — `PG_CONTEXT.md` global com secções por projeto

**Descrição**: um único `PG_CONTEXT.md` na raiz com marcadores por projeto:
```markdown
<!-- PG_MULTI:PROJECT:alpha-crm:START -->
...contexto do Alpha CRM...
<!-- PG_MULTI:PROJECT:alpha-crm:END -->
```

**Razões de rejeição:**
- `RISCO ALTO`: ficheiro cresce sem limite com o número de projetos; polui a janela de contexto dos agentes com informação de projetos irrelevantes.
- `RISCO ALTO`: escritas concorrentes de dois sync runs em projectos distintos podem corromper o ficheiro (edição do mesmo ficheiro em paralelo).
- `INCOMPATIBILIDADE`: o mecanismo `Replace-MarkedBlock` atual não suporta marcadores com prefixo de projeto sem refactor extenso.
- `RISCO OPERACIONAL`: um agente que lê contexto ambíguo pode misturar informação de projetos distintos — o problema exacto que PG-005 tenta resolver.

### 4.2 Opção C — Sub-directórios por projeto na raiz do repo (`projects/{key}/`)

**Descrição**: cada projeto tem a sua árvore completa na raiz:
```
projects/
  alpha-crm/
    PG_CONTEXT.md
    PG_SCOPE_INTAKE.yaml
    .pg/
      PG_SCOPE_SYNC.json
      ...
```

**Razões de rejeição:**
- `CUSTO ALTO`: todos os scripts têm `$repo` como raiz; seriam necessários `$repo/projects/{key}` como "repo virtual" — refactor extenso.
- `RISCO DE MIGRAÇÃO`: repos existentes teriam de ser reorganizados completamente.
- `COMPLEXIDADE OPERACIONAL`: agentes precisam de saber qual sub-directório é o "seu" projeto — introduz uma camada extra de descoberta não suportada pelos contratos actuais.
- `BREAKING CHANGE`: quebraria `pg_smoke_test_repo.ps1`, `pg_bootstrap_repo.ps1` e todos os scripts sem refactor significativo.

---

## 5. Tabela de trade-offs

| Dimensão | Opção A (recomendada) | Opção B (rejeitada) | Opção C (rejeitada) |
|---|---|---|---|
| **Complexidade de implementação** | Média — add `-ProjectKey` + função common | Baixa (1 ficheiro) mas com regex complexo | Alta — refactor profundo de todos os scripts |
| **Risco de colisão** | Nulo — paths disjuntos por key | Alto — escritas no mesmo ficheiro | Nulo — sub-árvores disjuntas |
| **Compatibilidade backward** | Total — legacy mode sem `PG_PROJECT_INDEX.json` | Parcial — marcadores novos mas 1 ficheiro | Quebra total — reorganização de repo |
| **Custo operacional** | Baixo — 1 param extra nos scripts | Médio — gestão de ficheiro monolítico | Alto — paths duplos para todo o lado |
| **Segurança semântica AI** | Alta — 1 contexto por projeto, isolado | Baixa — agente lê contexto de todos os projetos | Alta — sub-árvore isolada |
| **Auditabilidade** | Alta — git diff por projeto em `.pg/projects/{key}/` | Média — git diff num único ficheiro grande | Alta — sub-árvore isolada |
| **Onboarding de novo projeto** | 1 comando: `pg_bootstrap_repo.ps1 -ProjectKey` | Adicionar secção manualmente | Criar sub-directório manualmente |
| **Rollback** | Simples — remover pasta e entrada no index | Médio — editar secção no ficheiro global | Simples — remover sub-directório |
| **Escalabilidade (N projetos)** | O(N) pastas; sem degradação | O(N) linhas no mesmo ficheiro | O(N) sub-directórios |

---

## 6. Plano faseado

### F0 — Discovery ✅ CONCLUÍDO em 2026-05-27

- [x] Leitura completa da arquitectura actual
- [x] Identificação dos pontos de colisão
- [x] Proposta de 3 opções com análise de trade-offs
- [x] Produção deste contrato
- [x] **GATE**: contrato aprovado — decisões D1–D5 fechadas por Pedro Coelho em 2026-05-27
- [x] **GATE**: decisões em aberto (secção 7) todas fechadas

### F1 — Piloto (após aprovação do contrato)

**Âmbito:**
- Introduzir `PG_PROJECT_INDEX.json` com schema `2.0`
- Criar `pg_project_path_common.ps1` com `Resolve-PgProjectPath`
- Adicionar `-ProjectKey` a 5 scripts críticos:
  - `pg_bootstrap_repo.ps1`
  - `pg_build_pg_context.ps1`
  - `pg_apply_project_status_sync.ps1`
  - `pg_apply_scope_sync.ps1`
  - `pg_smoke_test_repo.ps1`
- Criar `pg_migrate_to_multiproject.ps1` para repos existentes
- Atualizar `AGENTS_SHARED.md` com instrução de descoberta multi-projeto
- Atualizar `PG_CONTEXT.md` template para suportar modo índice

**Critérios de aceitação F1:**
- `pg_smoke_test_repo.ps1` passa num repo single-project legacy (sem `PG_PROJECT_INDEX.json`)
- `pg_smoke_test_repo.ps1` passa num repo com 2 projetos registados
- Um agente consegue identificar e carregar o contexto correcto de cada projeto
- A migração de um repo legacy existente funciona sem perda de dados
- Nenhum script existente quebra em modo legacy

**Estimativa de esforço F1:** 3–5 dias de desenvolvimento + 1–2 dias de testes

### F2 — Generalização (após F1 validado em piloto)

**Âmbito:**
- Atualizar todos os restantes scripts `pg_validate_*.ps1` com `-ProjectKey`
- Atualizar `pg_log_token_consumption.ps1` para path por projeto
- Atualizar GitHub Actions workflows para suportar `project_key` como input
- Documentar onboarding multi-projeto no `README.md` e guias operacionais
- Atualizar `handoff/` com bundle de adoção multi-projeto
- Smoke tests de integração com N projetos (N >= 3)

**Critérios de aceitação F2:**
- Todos os scripts suportam `-ProjectKey` sem erros
- `pg_smoke_test_repo.ps1` valida todos os projetos registados num único pass
- GitHub Actions pode ser triggado por alterações a um projeto específico
- Um novo operador consegue fazer onboarding de um segundo projeto num repo existente sem ajuda oral

**Estimativa de esforço F2:** 5–8 dias de desenvolvimento + 2–3 dias de testes

---

## 7. Decisões — TODAS FECHADAS em 2026-05-27

Todas as decisões foram fechadas por Pedro Coelho em 2026-05-27.

### D1 — Localização de `PG_CONTEXT.md` por projeto `FECHADO`

**Decisão aprovada**: `projects/{project_key}/PG_CONTEXT.md` na raiz do repo (não dentro de `.pg/`).

Rationale confirmado: `.pg/` contém dados operacionais (JSON, JSONL); `PG_CONTEXT.md` é contexto AI — deve ser legível e editável fora do directório técnico.

Impacto em implementação: `pg_build_pg_context.ps1` escreve para `projects/{key}/PG_CONTEXT.md`; `pg_smoke_test_repo.ps1` valida a presença desse path em modo multi.

---

### D2 — Derivação do `project_key` `FECHADO`

**Decisão aprovada**: `project_key = slug(project_name)`, com unicidade garantida por `project_id` no `PG_PROJECT_INDEX.json`.

Formato do slug: lowercase, substituir espaços e não-alfanuméricos por `-`, colapsar `-` múltiplos, máx. 48 chars. Em colisão de slug, acrescentar sufixo numérico (`-2`, `-3`, ...).

O `project_id` Odoo é registado no índice e serve de âncora imutável mesmo que o `project_name` mude. O slug não muda após registo.

---

### D3 — Conteúdo do `PG_CONTEXT.md` raiz em modo multi `FECHADO`

**Decisão aprovada**: índice curto por projeto + link/path para o contexto dedicado.

Formato alvo:

```markdown
# PG_CONTEXT - Índice Global

> Em modo multi-projeto este ficheiro é apenas um índice.
> Identificar o projeto alvo e carregar projects/{key}/PG_CONTEXT.md.

## Projetos ativos

| Projeto | Key | Fase | Estado | Contexto |
|---|---|---|---|---|
| Alpha CRM | `alpha-crm` | Análise | Em curso | [PG_CONTEXT](projects/alpha-crm/PG_CONTEXT.md) |

Última actualização do índice: {timestamp}
```

Resumo por linha: `project_name`, `project_key`, `project_phase`, `status_summary` (truncado a 80 chars) e link relativo para o contexto. Gerado automaticamente por `pg_refresh_pg_context.ps1` em modo multi.

---

### D4 — Schema de tokens `FECHADO`

**Decisão aprovada**: manter schema actual de `consumption.jsonl` intacto; adicionar campo `project_key` opcional (string, pode ser omitido ou `null`).

Sem segundo ficheiro por projecto na F1. Um único `.pg/tokens/consumption.jsonl` por repo. O campo `project_key` no evento permite filtrar por projecto em análise posterior sem quebrar registos existentes.

Schema delta (campo adicional ao schema `1.0` existente):
```json
{ "project_key": "alpha-crm" }   // opcional; omitir se sessão transversal/framework
```

O validador `pg_validate_token_consumption.ps1` aceita eventos sem `project_key` (backward compatible). Em F2, pode-se adicionar validação opcional se `project_key` presente deve existir no `PG_PROJECT_INDEX.json`.

---

### D5 — Limite de projetos por repo `FECHADO`

**Decisão aprovada**: limite operacional recomendado de 20 projetos/repo; sem hard limit técnico na F1.

O limite de 20 é documentado no guia operacional como recomendação (acima disso, considerar repo separado por razões de contexto AI e legibilidade do índice). Não é validado pelo código na F1 — pode ser adicionado como warning em smoke test na F2.

---

## 8. Critérios de aceitação para tirar PG-005 de ADIADO

PG-005 só entra em implementação (F1) quando **todos** os seguintes critérios estiverem satisfeitos:

1. ✅ **Este contrato está aprovado** — decisões D1–D5 fechadas por Pedro Coelho em 2026-05-27.
2. ✅ **Decisões D1–D5 estão fechadas** — todas fechadas em 2026-05-27 (ver secção 7).
3. ✅ **Não existe bloqueio operacional activo** — PG-004 e anteriores totalmente fechados em 2026-05-27.
4. ⏳ **Estimativa de esforço F1 validada** — operador confirma disponibilidade para 3–5 dias de desenvolvimento.
5. ⏳ **Repo de piloto identificado** — pelo menos 1 repo real (não `_pg_template`) com 2 projetos para testar F1.

**Estado actual**: 3/5 critérios satisfeitos. Faltam critérios 4 e 5 para iniciar F1.

---

## 9. Riscos e impactos

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Slug `project_key` colidindo por nomes similares | Baixa | Médio | Lógica de sufixo numérico + validação no registo |
| Agentes ignoram índice global e lêem `PG_CONTEXT.md` raiz como contexto do projeto | Média | Alto | Instrução explícita em `AGENTS_SHARED.md`; índice inclui aviso |
| Migration script falhando em repos com customizações locais | Baixa | Médio | Dry-run mode + backup automático antes de migrar |
| GitHub Actions triggados por qualquer projeto em vez do correto | Média | Médio | Workflow filtra por `project_key` no path do artefacto modificado |
| `PG_PROJECT_INDEX.json` dessincronizado do filesystem | Baixa | Alto | `pg_smoke_test_repo.ps1` valida consistência index vs. filesystem |

---

## 9b. Spec de implementação Odoo (`pg_brodoo`)

Spec detalhada das alterações necessárias no addon `pg_brodoo` para suportar namespacing multi-projeto:

→ `docs/PG_005_BRODOO_CHANGE_SPEC.md`

---

## 10. Referências consultadas

### Artefactos do projecto
- `docs/PG_FRAMEWORK_IMPROVEMENT_BACKLOG.md` — definição de PG-005, critérios de aceitação, decisão ADIAR
- `docs/PG_CURRENT_WORKING_STATE.md` — estado pós-fecho de PG-004
- `docs/PG_004_OPERATIONAL_CLOSURE_CHECKLIST.md` — confirmação de fecho de PG-004 em 2026-05-27
- `templates/AGENTS_SHARED.md` — contrato partilhado dos agentes (regras de consulta)
- `templates/PG_CONTEXT.md` — template actual do contexto

### Scripts analisados
- `scripts/pg_bootstrap_repo.ps1` — lógica de criação de `.pg/` e paths actuais
- `scripts/pg_build_pg_context.ps1` — paths hardcoded de `PG_SCOPE_INTAKE.yaml` e `PG_CONTEXT.md`
- `scripts/pg_apply_project_status_sync.ps1` — path hardcoded de `PG_PROJECT_STATUS_SYNC.json`
- `scripts/pg_scope_sync_common.ps1` — contrato de validação; campo `project_id` confirmado como obrigatório
- `scripts/pg_smoke_test_repo.ps1` — inventário completo de paths hardcoded a actualizar

### Histórico de decisões relacionadas
- PG-004 discovery (2026-05-26): modelo pull-based com staging atómico — padrão a replicar para snapshots multi-projeto
