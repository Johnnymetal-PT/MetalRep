# PG_005_BRODOO_CHANGE_SPEC

## Metadados

| Campo | Valor |
|---|---|
| Item de backlog | `PG-005` |
| Fase | F1 — Piloto |
| Tipo | Spec de alterações no addon `pg_brodoo` |
| Estado | `APROVADO — PRONTO PARA IMPLEMENTAÇÃO` |
| Autor | Claude Code (Sonnet 4.6) — sessão 2026-05-27 |
| Depende de | `docs/PG_005_ARCHITECTURE_CONTRACT.md` (aprovado) |

---

## 1. Contexto e problema a resolver

O publisher do `pg_brodoo` (`github_repository_publisher.py`) publica todos os artefactos em **paths globais fixos**:

```python
SCOPE_SNAPSHOT_PATH    = '.pg/PG_SCOPE_SYNC.json'
STATUS_SNAPSHOT_PATH   = '.pg/PG_PROJECT_STATUS_SYNC.json'
PROJECT_CONTEXT_PATH   = 'PG_CONTEXT.md'
# ... etc
```

Se dois projetos Odoo distintos apontam para o mesmo repo e branch, o segundo sobrescreve o primeiro — sem aviso, sem colisão visível.

A solução aprovada (D1–D5): introduzir `project_key` por projeto, e publicar sob `.pg/projects/{project_key}/` em modo multi. Modo legacy (sem `project_key`) continua a funcionar intacto.

---

## 2. Princípios de implementação

- **Backward compatibility**: projetos sem `pg_project_key` → comportamento actual sem qualquer alteração.
- **Sem double migration**: nenhuma migração automática de dados JSON existentes no GitHub. Projetos existentes continuam em legacy mode até serem explicitamente migrados.
- **`project_key` imutável após primeiro publish**: impedir edição após o primeiro sync para garantir consistência do namespace no repo.
- **F1 scope mínimo**: não incluir geração do índice global `PG_CONTEXT.md` (raiz) — fica para F2.

---

## 3. Mapa de paths: legacy vs. multi-projeto

| Artefacto | Path legacy | Path multi-projeto |
|---|---|---|
| Scope snapshot | `.pg/PG_SCOPE_SYNC.json` | `.pg/projects/{key}/PG_SCOPE_SYNC.json` |
| Status snapshot | `.pg/PG_PROJECT_STATUS_SYNC.json` | `.pg/projects/{key}/PG_PROJECT_STATUS_SYNC.json` |
| Decisions snapshot | `.pg/PG_DECISIONS_SYNC.json` | `.pg/projects/{key}/PG_DECISIONS_SYNC.json` |
| Risks snapshot | `.pg/PG_RISKS_SYNC.json` | `.pg/projects/{key}/PG_RISKS_SYNC.json` |
| Deliveries snapshot | `.pg/PG_DELIVERIES_SYNC.json` | `.pg/projects/{key}/PG_DELIVERIES_SYNC.json` |
| Requirements snapshot | `.pg/PG_REQUIREMENTS_SYNC.json` | `.pg/projects/{key}/PG_REQUIREMENTS_SYNC.json` |
| Project plan snapshot | `.pg/PG_PROJECT_PLAN_SYNC.json` | `.pg/projects/{key}/PG_PROJECT_PLAN_SYNC.json` |
| Budget snapshot | `.pg/PG_BUDGET_SYNC.json` | `.pg/projects/{key}/PG_BUDGET_SYNC.json` |
| Mirror: project | `.pg/project/project.json` | `.pg/projects/{key}/project/project.json` |
| Mirror: planning | `.pg/planning/planning.json` | `.pg/projects/{key}/planning/planning.json` |
| Mirror: tasks | `.pg/tasks/tasks.json` | `.pg/projects/{key}/tasks/tasks.json` |
| Mirror: chatter | `.pg/chatter/chatter.json` | `.pg/projects/{key}/chatter/chatter.json` |
| Mirror: attachments | `.pg/attachments/attachments.json` | `.pg/projects/{key}/attachments/attachments.json` |
| Mirror: history | `.pg/history/events.jsonl` | `.pg/projects/{key}/history/events.jsonl` |
| Context AI | `PG_CONTEXT.md` | `projects/{key}/PG_CONTEXT.md` |
| Project index | *(não existe)* | `.pg/PG_PROJECT_INDEX.json` |

---

## 4. Alterações necessárias — listagem por ficheiro

### 4.1 `models/project_project.py` — novo campo `pg_project_key`

**Tipo**: campo novo + métodos auxiliares + constraint

```python
# Novo campo — após os campos pg_budget_* existentes (ou junto dos campos pg_repo*)
pg_project_key = fields.Char(
    string='PG Project Key',
    copy=False,
    index=True,
    help=(
        'Unique key identifying this project in the GitHub repository namespace. '
        'Auto-derived from project name as a lowercase slug. '
        'Immutable after first successful publish.'
    ),
)
```

**Método de derivação de slug** (privado, sem side effects):

```python
@api.model
def _pg_derive_project_key(self, name):
    """Derive a stable URL-safe slug from a project name."""
    import re
    import unicodedata
    normalized = unicodedata.normalize('NFKD', name or '').encode('ascii', 'ignore').decode('ascii')
    slug = re.sub(r'[^a-z0-9]+', '-', normalized.lower())
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug[:48] or 'project'
```

**Método público — obter ou derivar key para um projecto** (chamado pelos serviços antes de publicar):

```python
def _pg_resolve_project_key(self):
    """Return the current project_key, or None if not yet assigned (legacy mode)."""
    self.ensure_one()
    return (self.pg_project_key or '').strip() or None
```

**Constraint: unicidade por repo + branch**:

```python
@api.constrains('pg_project_key', 'pg_repository_id', 'pg_repo_branch')
def _check_pg_project_key_unique(self):
    for project in self:
        key = (project.pg_project_key or '').strip()
        if not key:
            continue
        existing = self.search([
            ('pg_project_key', '=', key),
            ('pg_repository_id', '=', project.pg_repository_id.id),
            ('pg_repo_branch', '=', project.pg_repo_branch),
            ('id', '!=', project.id),
        ])
        if existing:
            raise ValidationError(
                _("Project key '%s' is already used by another project in the same repository and branch.") % key
            )
```

**Constraint: formato de slug**:

```python
@api.constrains('pg_project_key')
def _check_pg_project_key_format(self):
    import re
    for project in self:
        key = (project.pg_project_key or '').strip()
        if key and not re.fullmatch(r'[a-z0-9][a-z0-9\-]{0,47}', key):
            raise ValidationError(
                _("Project key must be a lowercase alphanumeric slug (letters, digits and hyphens only, max 48 chars, must start with a letter or digit).")
            )
```

**`_pg_mirror_sync_relevant_fields` — adicionar `pg_project_key`**:

```python
# Adicionar ao conjunto existente:
'pg_project_key',
```

**Não fazer**: não calcular `pg_project_key` automaticamente em `create()` ou `write()`. O operador define o key manualmente (ou via wizard de onboarding, F2). A auto-derivação pode ser sugerida no UI via `@api.onchange` mas não deve ser persistida automaticamente.

**`@api.onchange` sugestivo** (não obrigatório, melhora UX):

```python
@api.onchange('name')
def _onchange_name_suggest_project_key(self):
    if self.name and not self.pg_project_key:
        self.pg_project_key = self._pg_derive_project_key(self.name)
```

---

### 4.2 `services/github_repository_publisher.py` — paths dinâmicos

**Tipo**: refactor das constantes de classe para método; novo método `_build_paths`; novo parâmetro no `__init__`

**Mudança principal**: o publisher passa a receber `project_key` no construtor. Quando `project_key` é `None` ou vazio, usa os paths legacy. Quando está presente, usa os paths namespaced.

```python
class GitHubRepositoryPublisher:

    # Nomes canónicos dos artefactos (mantidos para referência interna)
    _SCOPE_ARTIFACT          = 'PG_SCOPE_SYNC.json'
    _STATUS_ARTIFACT         = 'PG_PROJECT_STATUS_SYNC.json'
    _DECISIONS_ARTIFACT      = 'PG_DECISIONS_SYNC.json'
    _RISKS_ARTIFACT          = 'PG_RISKS_SYNC.json'
    _DELIVERIES_ARTIFACT     = 'PG_DELIVERIES_SYNC.json'
    _REQUIREMENTS_ARTIFACT   = 'PG_REQUIREMENTS_SYNC.json'
    _PROJECT_PLAN_ARTIFACT   = 'PG_PROJECT_PLAN_SYNC.json'
    _BUDGET_ARTIFACT         = 'PG_BUDGET_SYNC.json'

    # Paths legacy (backward compat — usados quando project_key é None)
    _LEGACY = {
        'scope':          '.pg/PG_SCOPE_SYNC.json',
        'status':         '.pg/PG_PROJECT_STATUS_SYNC.json',
        'decisions':      '.pg/PG_DECISIONS_SYNC.json',
        'risks':          '.pg/PG_RISKS_SYNC.json',
        'deliveries':     '.pg/PG_DELIVERIES_SYNC.json',
        'requirements':   '.pg/PG_REQUIREMENTS_SYNC.json',
        'project_plan':   '.pg/PG_PROJECT_PLAN_SYNC.json',
        'budget':         '.pg/PG_BUDGET_SYNC.json',
        'mirror_project': '.pg/project/project.json',
        'mirror_planning':'.pg/planning/planning.json',
        'mirror_tasks':   '.pg/tasks/tasks.json',
        'mirror_chatter': '.pg/chatter/chatter.json',
        'mirror_attachments': '.pg/attachments/attachments.json',
        'mirror_history': '.pg/history/events.jsonl',
        'context':        'PG_CONTEXT.md',
    }

    PROJECT_INDEX_PATH = '.pg/PG_PROJECT_INDEX.json'

    def __init__(self, env, project_key=None):
        self.env = env
        self.github_service = GitHubService(env)
        self._project_key = (project_key or '').strip() or None

    def _path(self, artifact_key):
        """Return the resolved path for an artifact, namespaced by project_key if set."""
        if not self._project_key:
            return self._LEGACY[artifact_key]
        # Snapshot JSONs: .pg/projects/{key}/ARTIFACT.json
        if artifact_key in {'scope', 'status', 'decisions', 'risks', 'deliveries',
                             'requirements', 'project_plan', 'budget'}:
            artifact_name = {
                'scope':        'PG_SCOPE_SYNC.json',
                'status':       'PG_PROJECT_STATUS_SYNC.json',
                'decisions':    'PG_DECISIONS_SYNC.json',
                'risks':        'PG_RISKS_SYNC.json',
                'deliveries':   'PG_DELIVERIES_SYNC.json',
                'requirements': 'PG_REQUIREMENTS_SYNC.json',
                'project_plan': 'PG_PROJECT_PLAN_SYNC.json',
                'budget':       'PG_BUDGET_SYNC.json',
            }[artifact_key]
            return f'.pg/projects/{self._project_key}/{artifact_name}'
        # Mirror sub-paths: .pg/projects/{key}/sub/file.json
        if artifact_key in {'mirror_project', 'mirror_planning', 'mirror_tasks',
                             'mirror_chatter', 'mirror_attachments', 'mirror_history'}:
            sub = {
                'mirror_project':     'project/project.json',
                'mirror_planning':    'planning/planning.json',
                'mirror_tasks':       'tasks/tasks.json',
                'mirror_chatter':     'chatter/chatter.json',
                'mirror_attachments': 'attachments/attachments.json',
                'mirror_history':     'history/events.jsonl',
            }[artifact_key]
            return f'.pg/projects/{self._project_key}/{sub}'
        # Context AI: projects/{key}/PG_CONTEXT.md
        if artifact_key == 'context':
            return f'projects/{self._project_key}/PG_CONTEXT.md'
        raise ValueError(f'Unknown artifact key: {artifact_key}')

    # Propriedades públicas de path (para uso pelos serviços ao registar snapshot_path nos sync runs)
    @property
    def scope_snapshot_path(self):       return self._path('scope')
    @property
    def status_snapshot_path(self):      return self._path('status')
    @property
    def decisions_snapshot_path(self):   return self._path('decisions')
    @property
    def risks_snapshot_path(self):       return self._path('risks')
    @property
    def deliveries_snapshot_path(self):  return self._path('deliveries')
    @property
    def requirements_snapshot_path(self):return self._path('requirements')
    @property
    def project_plan_snapshot_path(self):return self._path('project_plan')
    @property
    def budget_snapshot_path(self):      return self._path('budget')
    @property
    def project_context_path(self):      return self._path('context')
```

**Todos os métodos `publish_*` passam a usar `self._path(...)` em vez das constantes**:

```python
def publish_project_scope_snapshot(self, repository, branch_name, payload):
    return self._publish_snapshot(
        repository,
        self._path('scope'),      # ← antes era self.SCOPE_SNAPSHOT_PATH
        branch_name,
        payload,
        'chore(pg-sync): refresh project scope from odoo',
    )
# ... idem para todos os outros publish_*
```

**Novo método: `update_project_index`** — regista/actualiza o projecto no `PG_PROJECT_INDEX.json`:

```python
def update_project_index(self, repository, branch_name, project_id, project_key, project_name, odoo_source=None):
    """
    Upsert this project in .pg/PG_PROJECT_INDEX.json.
    Called once per project on first publish, or when key/name changes.
    Does nothing in legacy mode (no project_key).
    """
    if not self._project_key:
        return

    import json
    from datetime import datetime, timezone

    existing_content = self.github_service.get_repository_file_text(
        repository, self.PROJECT_INDEX_PATH, branch=branch_name,
    )

    if existing_content:
        try:
            index = json.loads(existing_content)
        except (ValueError, TypeError):
            index = {'schema_version': '2.0', 'registry': []}
    else:
        index = {'schema_version': '2.0', 'registry': []}

    registry = index.get('registry') or []

    # Find existing entry for this project_id
    existing_entry = next(
        (e for e in registry if str(e.get('project_id')) == str(project_id)),
        None,
    )

    now_iso = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    if existing_entry:
        existing_entry['project_key'] = project_key
        existing_entry['project_name'] = project_name
        existing_entry['status'] = 'active'
        if odoo_source:
            existing_entry['odoo_source'] = odoo_source
    else:
        new_entry = {
            'project_key': project_key,
            'project_id': project_id,
            'project_name': project_name,
            'registered_at': now_iso,
            'status': 'active',
        }
        if odoo_source:
            new_entry['odoo_source'] = odoo_source
        registry.append(new_entry)

    index['registry'] = sorted(registry, key=lambda e: e.get('project_key', ''))

    content = json.dumps(index, ensure_ascii=True, indent=2, sort_keys=True) + '\n'
    return self.github_service.upsert_repository_file(
        repository,
        self.PROJECT_INDEX_PATH,
        content,
        'chore(pg-sync): update project registry index',
        branch=branch_name,
    )
```

---

### 4.3 Todos os serviços de sync — injectar `project_key` no publisher

**Padrão**: cada serviço (`ProjectScopeSyncService`, `ProjectStatusSyncService`, `ProjectDecisionsSyncService`, `ProjectRisksSyncService`, `ProjectDeliveriesSyncService`, `ProjectRequirementsSyncService`, `ProjectPlanSyncService`, `ProjectBudgetSyncService`, `ProjectMirrorSyncService`) instância o publisher **com** o `project_key` do projecto.

**Regra**: o publisher deve ser instanciado **por projecto**, dentro do método `process_run`, não no `__init__` do serviço.

**Mudança nos serviços** (padrão comum a todos):

```python
# ANTES (no __init__ do serviço):
self.publisher = GitHubRepositoryPublisher(env)

# DEPOIS: remover do __init__; criar por projecto no process_run:
def _build_publisher(self, project):
    """Build a publisher scoped to this project's key (or legacy if no key)."""
    project_key = project._pg_resolve_project_key()
    return GitHubRepositoryPublisher(self.env, project_key=project_key)
```

E em `process_run` (ou equivalente):
```python
publisher = self._build_publisher(project)
```

---

### 4.4 `snapshot_path` nos sync run models — usar path resolvido

Os modelos `pg.project.scope.sync.run`, `pg.project.status.sync.run`, etc. registam `snapshot_path` no registo do run. Actualmente os serviços hardcoded esse valor:

```python
# Antes (em project_scope_sync_service.py, linha ~58):
'snapshot_path': '.pg/PG_SCOPE_SYNC.json',
```

**Após a mudança**: o `snapshot_path` no run deve ser o path real calculado pelo publisher:

```python
publisher = self._build_publisher(project)
# ...
'snapshot_path': publisher.scope_snapshot_path,  # resolvido com ou sem namespace
```

Idem para todos os outros serviços: usar a propriedade correspondente do publisher.

---

### 4.5 `services/project_scope_sync_service.py` — update_project_index no primeiro publish

No `process_run`, após o publish bem-sucedido do snapshot, chamar `update_project_index` se `project_key` estiver definido:

```python
# Após publish bem-sucedido:
if project_key:
    publisher.update_project_index(
        repository=project.pg_repository_id,
        branch_name=project.pg_repo_branch,
        project_id=project.id,
        project_key=project_key,
        project_name=project.name,
    )
```

Fazer o mesmo nos outros serviços de sync (pelo menos scope e mirror para a F1; os restantes na F2).

---

### 4.6 `models/pg_project_scope_sync_run.py` (e equivalentes) — sem alteração de schema

Os sync run models têm já um campo `snapshot_path = fields.Char(...)`. Não é necessário alterar o schema — apenas o valor que lhe é atribuído muda (path namespaced em vez de path fixo).

Verificar se os outros sync run models (`pg.project.status.sync.run`, etc.) têm campo `snapshot_path`. Se não tiverem, não é necessário adicionar para F1.

---

### 4.7 `views/project_project_views.xml` — campo `pg_project_key` visível

Adicionar `pg_project_key` ao form view do projecto, junto dos campos de repositório:

```xml
<!-- Junto de pg_repository_id e pg_repo_branch -->
<field name="pg_project_key"
       placeholder="ex: alpha-crm"
       attrs="{'readonly': [('pg_scope_sync_last_published_at', '!=', False)]}"/>
```

O campo fica editável até ao primeiro publish. Após o primeiro publish (`pg_scope_sync_last_published_at` preenchido), fica read-only.

**Alternativamente** (mais robusto): usar um campo computado `pg_project_key_locked` para controlar o readonly, verificando se algum sync já foi feito para este projecto.

---

### 4.8 Migração de base de dados — `migrations/19.0.1.1.0/`

```
pg_brodoo/
  migrations/
    19.0.1.1.0/
      pre-migrate.py    # (vazio ou ausente — não há pré-requisitos)
      post-migrate.py   # (vazio — campo Char sem default não precisa de backfill)
```

O campo `pg_project_key = fields.Char(...)` sem `required=True` e sem `default` é adicionado com `NULL` para todos os registos existentes → backward compat imediato. Não é necessário backfill automático.

**Versão do módulo**: bump de `19.0.1.0.0` → `19.0.1.1.0` no `__manifest__.py`.

---

## 5. Alterações que ficam para F2 (fora de scope de F1)

| Funcionalidade | Motivo de adiamento |
|---|---|
| Geração do `PG_CONTEXT.md` raiz como índice global | Requer lógica de merge no mirror sync; impacto alto |
| `@api.onchange` automático de `pg_project_key` a partir do nome | Pode entrar em F1 como melhoria UX; não é bloqueante |
| Wizard de onboarding multi-projeto com validação de key | Novo wizard, fora de scope de F1 |
| Validação do `PG_PROJECT_INDEX.json` no smoke test do lado do repo | Script PowerShell, não Odoo |
| `pg_effort_sync` — namespace | Serviço ainda não tem publisher directo; adiado |
| Auto-migration de projetos legacy existentes (move JSON no GitHub) | Operação destrutiva; requer decisão separada |

---

## 6. Sequência de implementação recomendada (para Codex)

1. **Migração**: criar `migrations/19.0.1.1.0/` e bump de versão no `__manifest__.py`.
2. **Campo**: adicionar `pg_project_key` ao `models/project_project.py` com método `_pg_derive_project_key`, `_pg_resolve_project_key`, constraint de unicidade e constraint de formato.
3. **Publisher**: refactor de `services/github_repository_publisher.py` — `project_key` no `__init__`, `_path()` central, propriedades de path, `update_project_index`.
4. **Serviços**: extrair `_build_publisher(project)` em cada serviço; remover `self.publisher` do `__init__`; usar `publisher.scope_snapshot_path` etc. no `snapshot_path` dos runs.
5. **`update_project_index`**: chamar nos `process_run` de scope sync e mirror sync após publish bem-sucedido.
6. **Views**: adicionar `pg_project_key` ao form do projecto.
7. **Tests**: adicionar testes para:
   - derivação de slug (`_pg_derive_project_key`)
   - path resolution com e sem `project_key`
   - constraint de unicidade de `project_key` por repo+branch
   - `update_project_index` — criar e actualizar

---

## 7. Testes obrigatórios para aceitar F1

| Teste | Critério |
|---|---|
| `pg_project_key` vazio → publisher usa paths legacy (backward compat) | Publisher retorna `.pg/PG_SCOPE_SYNC.json` |
| `pg_project_key = 'alpha-crm'` → publisher usa paths namespaced | Publisher retorna `.pg/projects/alpha-crm/PG_SCOPE_SYNC.json` |
| Dois projectos com o mesmo key no mesmo repo+branch → ValidationError | Constraint dispara |
| Key com formato inválido (maiúsculas, espaços) → ValidationError | Constraint de formato dispara |
| `update_project_index` sem `PG_PROJECT_INDEX.json` existente → cria novo | JSON criado com schema_version 2.0 |
| `update_project_index` com projecto já registado → actualiza entry | Entry existente actualizada sem duplicado |
| Sync run registada com `snapshot_path` namespaced | `pg.project.scope.sync.run.snapshot_path` tem o path correcto |
| Projecto legacy (sem key) publica normalmente | Sem regressão |

---

## 8. Ficheiros a tocar na F1

| Ficheiro | Tipo de alteração |
|---|---|
| `pg_brodoo/__manifest__.py` | bump versão para `19.0.1.1.0` |
| `pg_brodoo/migrations/19.0.1.1.0/post-migrate.py` | novo (pode ser vazio) |
| `pg_brodoo/models/project_project.py` | campo + métodos + constraints + onchange |
| `pg_brodoo/services/github_repository_publisher.py` | refactor paths + `update_project_index` |
| `pg_brodoo/services/project_scope_sync_service.py` | `_build_publisher` + `update_project_index` call |
| `pg_brodoo/services/project_status_sync_service.py` | `_build_publisher` |
| `pg_brodoo/services/project_decisions_sync_service.py` | `_build_publisher` |
| `pg_brodoo/services/project_risks_sync_service.py` | `_build_publisher` |
| `pg_brodoo/services/project_deliveries_sync_service.py` | `_build_publisher` |
| `pg_brodoo/services/project_requirements_sync_service.py` | `_build_publisher` |
| `pg_brodoo/services/project_plan_sync_service.py` | `_build_publisher` |
| `pg_brodoo/services/project_budget_sync_service.py` | `_build_publisher` |
| `pg_brodoo/services/project_mirror_sync_service.py` | `_build_publisher` + `update_project_index` call |
| `pg_brodoo/views/project_project_views.xml` | campo `pg_project_key` |
| `pg_brodoo/tests/test_sync_services.py` | testes de namespacing |
| `pg_brodoo/tests/test_payload_builders.py` | confirmar que builders não dependem de path |
