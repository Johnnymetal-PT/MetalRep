# AGENTS — PG-005 F1: Namespacing multi-projeto no pg_brodoo

## Papel deste ficheiro

Este `AGENTS.md` substitui temporariamente o contrato padrão do projeto durante a implementação de PG-005 F1.
O seu único objetivo é implementar o namespacing multi-projeto no addon `pg_brodoo`, conforme o contrato arquitetural aprovado.

Quando F1 estiver concluído e testado, este ficheiro deve ser removido e o `AGENTS.md` padrão do projeto retomado.

## Repo e contexto

- Repo: `_pg_template` (ou repo de piloto com o código do `pg_brodoo`)
- Branch alvo: branch de feature (ex: `feat/pg-005-f1-multiproject`)
- Addon alvo: `pg_brodoo/`
- Spec completa: `docs/PG_005_BRODOO_CHANGE_SPEC.md`
- Contrato arquitetural: `docs/PG_005_ARCHITECTURE_CONTRACT.md`

## Objetivo

Adicionar suporte a múltiplos projetos Odoo no mesmo repositório GitHub e branch, sem colisão de artefactos.

A mudança central:
- Cada `project.project` pode ter um `pg_project_key` (slug único por repo+branch).
- Quando definido, todos os artefactos são publicados sob `.pg/projects/{project_key}/` em vez dos paths globais atuais.
- Projetos sem `pg_project_key` continuam exatamente como hoje (modo legacy — zero regressão).

## Restrições absolutas

1. **Não quebrar projetos legacy**: qualquer projeto sem `pg_project_key` deve funcionar exatamente como antes.
2. **Não implementar F2**: não gerar o índice global `PG_CONTEXT.md` na raiz — fica para F2.
3. **Não migrar dados existentes no GitHub**: não mover JSONs já publicados — projetos existentes ficam em legacy mode.
4. **Não alterar o schema dos sync run models** além do necessário (o campo `snapshot_path` já existe).
5. **Não alterar `vendor/odoo_src`** — é read-only.
6. **Testes obrigatórios antes de fechar**: ver secção "Critérios de aceitação".

---

## Sequência de implementação obrigatória

Seguir esta ordem. Cada passo tem um check de validação antes de avançar.

### Passo 1 — Bump de versão e migração

**Ficheiros:**
- `pg_brodoo/__manifest__.py` — versão de `19.0.1.0.0` para `19.0.1.1.0`
- `pg_brodoo/migrations/19.0.1.1.0/post-migrate.py` — criar ficheiro (pode estar vazio; o campo Char sem default não precisa backfill)

```python
# pg_brodoo/migrations/19.0.1.1.0/post-migrate.py
# Campo pg_project_key adicionado como Char nullable — sem backfill necessário.
```

**Check**: `__manifest__.py` tem `'version': '19.0.1.1.0'` e a pasta `migrations/19.0.1.1.0/` existe.

---

### Passo 2 — Campo `pg_project_key` e métodos em `project_project.py`

**Ficheiro**: `pg_brodoo/models/project_project.py`

**2a) Imports adicionais** no topo do ficheiro:
```python
import re
import unicodedata
```

**2b) Campo novo** — adicionar junto dos campos `pg_repo*` existentes:
```python
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

**2c) Método de derivação de slug** — adicionar como `@api.model`:
```python
@api.model
def _pg_derive_project_key(self, name):
    """Derive a stable URL-safe slug from a project name (max 48 chars)."""
    normalized = unicodedata.normalize('NFKD', name or '').encode('ascii', 'ignore').decode('ascii')
    slug = re.sub(r'[^a-z0-9]+', '-', normalized.lower())
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug[:48] or 'project'
```

**2d) Método de resolução** — chamado pelos serviços antes de publicar:
```python
def _pg_resolve_project_key(self):
    """Return the stored project_key, or None if in legacy mode (key not set)."""
    self.ensure_one()
    return (self.pg_project_key or '').strip() or None
```

**2e) `@api.onchange` sugestivo** — não persiste automaticamente, apenas sugere:
```python
@api.onchange('name')
def _onchange_name_suggest_project_key(self):
    if self.name and not self.pg_project_key:
        self.pg_project_key = self._pg_derive_project_key(self.name)
```

**2f) Constraint de formato**:
```python
@api.constrains('pg_project_key')
def _check_pg_project_key_format(self):
    for project in self:
        key = (project.pg_project_key or '').strip()
        if key and not re.fullmatch(r'[a-z0-9][a-z0-9\-]{0,47}', key):
            raise ValidationError(
                _("Project key must be a lowercase alphanumeric slug "
                  "(letters, digits and hyphens only, max 48 chars, "
                  "must start with a letter or digit).")
            )
```

**2g) Constraint de unicidade por repo+branch**:
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
                _("Project key '%s' is already used by another project "
                  "in the same repository and branch.") % key
            )
```

**2h) Adicionar `pg_project_key` a `_pg_mirror_sync_relevant_fields`**:
```python
# Adicionar ao conjunto retornado pelo método:
'pg_project_key',
```

**Check**: `python -c "import ast; ast.parse(open('pg_brodoo/models/project_project.py').read()); print('OK')"` sem erro.

---

### Passo 3 — Refactor do publisher

**Ficheiro**: `pg_brodoo/services/github_repository_publisher.py`

Substituir todo o conteúdo pelo seguinte (manter os métodos `_publish_snapshot` e `_publish_text_file` existentes, apenas adicionar/modificar o resto):

**3a) Remover as constantes de classe actuais** (`SCOPE_SNAPSHOT_PATH`, etc.) e substituir por:

```python
class GitHubRepositoryPublisher:

    # Paths legacy — usados quando project_key é None (backward compat)
    _LEGACY = {
        'scope':              '.pg/PG_SCOPE_SYNC.json',
        'status':             '.pg/PG_PROJECT_STATUS_SYNC.json',
        'decisions':          '.pg/PG_DECISIONS_SYNC.json',
        'risks':              '.pg/PG_RISKS_SYNC.json',
        'deliveries':         '.pg/PG_DELIVERIES_SYNC.json',
        'requirements':       '.pg/PG_REQUIREMENTS_SYNC.json',
        'project_plan':       '.pg/PG_PROJECT_PLAN_SYNC.json',
        'budget':             '.pg/PG_BUDGET_SYNC.json',
        'mirror_project':     '.pg/project/project.json',
        'mirror_planning':    '.pg/planning/planning.json',
        'mirror_tasks':       '.pg/tasks/tasks.json',
        'mirror_chatter':     '.pg/chatter/chatter.json',
        'mirror_attachments': '.pg/attachments/attachments.json',
        'mirror_history':     '.pg/history/events.jsonl',
        'context':            'PG_CONTEXT.md',
    }

    # Nomes dos ficheiros de snapshot (sem path) — usados na resolução namespaced
    _SNAPSHOT_FILES = {
        'scope':        'PG_SCOPE_SYNC.json',
        'status':       'PG_PROJECT_STATUS_SYNC.json',
        'decisions':    'PG_DECISIONS_SYNC.json',
        'risks':        'PG_RISKS_SYNC.json',
        'deliveries':   'PG_DELIVERIES_SYNC.json',
        'requirements': 'PG_REQUIREMENTS_SYNC.json',
        'project_plan': 'PG_PROJECT_PLAN_SYNC.json',
        'budget':       'PG_BUDGET_SYNC.json',
    }

    # Sub-paths dos mirror artifacts (sem prefixo .pg/)
    _MIRROR_SUBPATHS = {
        'mirror_project':     'project/project.json',
        'mirror_planning':    'planning/planning.json',
        'mirror_tasks':       'tasks/tasks.json',
        'mirror_chatter':     'chatter/chatter.json',
        'mirror_attachments': 'attachments/attachments.json',
        'mirror_history':     'history/events.jsonl',
    }

    PROJECT_INDEX_PATH = '.pg/PG_PROJECT_INDEX.json'

    def __init__(self, env, project_key=None):
        self.env = env
        self.github_service = GitHubService(env)
        self._project_key = (project_key or '').strip() or None

    def _path(self, artifact_key):
        """Resolve the GitHub path for an artifact, namespaced by project_key if set."""
        if not self._project_key:
            return self._LEGACY[artifact_key]
        if artifact_key in self._SNAPSHOT_FILES:
            return f'.pg/projects/{self._project_key}/{self._SNAPSHOT_FILES[artifact_key]}'
        if artifact_key in self._MIRROR_SUBPATHS:
            return f'.pg/projects/{self._project_key}/{self._MIRROR_SUBPATHS[artifact_key]}'
        if artifact_key == 'context':
            return f'projects/{self._project_key}/PG_CONTEXT.md'
        raise ValueError(f'Unknown artifact key: {artifact_key}')

    # Propriedades públicas de path — usadas pelos serviços para registar snapshot_path nos runs
    @property
    def scope_snapshot_path(self):        return self._path('scope')
    @property
    def status_snapshot_path(self):       return self._path('status')
    @property
    def decisions_snapshot_path(self):    return self._path('decisions')
    @property
    def risks_snapshot_path(self):        return self._path('risks')
    @property
    def deliveries_snapshot_path(self):   return self._path('deliveries')
    @property
    def requirements_snapshot_path(self): return self._path('requirements')
    @property
    def project_plan_snapshot_path(self): return self._path('project_plan')
    @property
    def budget_snapshot_path(self):       return self._path('budget')
    @property
    def project_context_path(self):       return self._path('context')
```

**3b) Todos os métodos `publish_*`** passam a usar `self._path(...)`:

```python
def publish_project_scope_snapshot(self, repository, branch_name, payload):
    return self._publish_snapshot(
        repository, self._path('scope'), branch_name, payload,
        'chore(pg-sync): refresh project scope from odoo',
    )

def publish_project_status_snapshot(self, repository, branch_name, payload):
    return self._publish_snapshot(
        repository, self._path('status'), branch_name, payload,
        'chore(pg-sync): refresh project status from odoo',
    )

def publish_project_decisions_snapshot(self, repository, branch_name, payload):
    return self._publish_snapshot(
        repository, self._path('decisions'), branch_name, payload,
        'chore(pg-sync): refresh project decisions from odoo',
    )

def publish_project_risks_snapshot(self, repository, branch_name, payload):
    return self._publish_snapshot(
        repository, self._path('risks'), branch_name, payload,
        'chore(pg-sync): refresh project risks from odoo',
    )

def publish_project_deliveries_snapshot(self, repository, branch_name, payload):
    return self._publish_snapshot(
        repository, self._path('deliveries'), branch_name, payload,
        'chore(pg-sync): refresh project deliveries from odoo',
    )

def publish_project_requirements_snapshot(self, repository, branch_name, payload):
    return self._publish_snapshot(
        repository, self._path('requirements'), branch_name, payload,
        'chore(pg-sync): refresh project requirements from odoo',
    )

def publish_project_plan_snapshot(self, repository, branch_name, payload):
    return self._publish_snapshot(
        repository, self._path('project_plan'), branch_name, payload,
        'chore(pg-sync): refresh project plan from odoo',
    )

def publish_project_budget_snapshot(self, repository, branch_name, payload):
    return self._publish_snapshot(
        repository, self._path('budget'), branch_name, payload,
        'chore(pg-sync): refresh project budget from odoo',
    )

def publish_project_mirror_payload(self, repository, branch_name, payload):
    return self._publish_snapshot(
        repository, self._path('mirror_project'), branch_name, payload,
        'chore(pg-mirror): refresh project context from odoo',
    )

def publish_planning_mirror_payload(self, repository, branch_name, payload):
    return self._publish_snapshot(
        repository, self._path('mirror_planning'), branch_name, payload,
        'chore(pg-mirror): refresh planning context from odoo',
    )

def publish_tasks_mirror_payload(self, repository, branch_name, payload):
    return self._publish_snapshot(
        repository, self._path('mirror_tasks'), branch_name, payload,
        'chore(pg-mirror): refresh task context from odoo',
    )

def publish_chatter_mirror_payload(self, repository, branch_name, payload):
    return self._publish_snapshot(
        repository, self._path('mirror_chatter'), branch_name, payload,
        'chore(pg-mirror): refresh chatter context from odoo',
    )

def publish_attachments_mirror_payload(self, repository, branch_name, payload):
    return self._publish_snapshot(
        repository, self._path('mirror_attachments'), branch_name, payload,
        'chore(pg-mirror): refresh attachment metadata from odoo',
    )

def append_project_mirror_history_event(self, repository, branch_name, payload):
    existing_content = self.github_service.get_repository_file_text(
        repository, self._path('mirror_history'), branch=branch_name,
    )
    event_line = json.dumps(payload, ensure_ascii=True, sort_keys=True) + '\n'
    if existing_content:
        content = existing_content
        if not content.endswith('\n'):
            content += '\n'
        content += event_line
    else:
        content = event_line
    return self._publish_text_file(
        repository, self._path('mirror_history'), branch_name, content,
        'chore(pg-mirror): append project history event from odoo',
    )

def publish_project_context(self, repository, branch_name, content):
    return self._publish_text_file(
        repository, self._path('context'), branch_name, content,
        'chore(pg-mirror): refresh PG_CONTEXT from mirror artifacts',
    )
```

**3c) Novo método `update_project_index`** — adicionar ao publisher:

```python
def update_project_index(self, repository, branch_name, project_id, project_key, project_name, odoo_source=None):
    """
    Upsert this project in .pg/PG_PROJECT_INDEX.json.
    Called after the first successful publish of a namespaced project.
    Does nothing in legacy mode (no project_key).
    """
    if not self._project_key:
        return None

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

    registry = list(index.get('registry') or [])
    existing_entry = next(
        (e for e in registry if str(e.get('project_id')) == str(project_id)),
        None,
    )
    now_iso = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    if existing_entry:
        existing_entry.update({
            'project_key': project_key,
            'project_name': project_name,
            'status': 'active',
            **(({'odoo_source': odoo_source}) if odoo_source else {}),
        })
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
        repository, self.PROJECT_INDEX_PATH, content,
        'chore(pg-sync): update project registry index',
        branch=branch_name,
    )
```

**Check**: `python -c "import ast; ast.parse(open('pg_brodoo/services/github_repository_publisher.py').read()); print('OK')"` sem erro.

---

### Passo 4 — Padrão `_build_publisher` em todos os serviços de sync

**Ficheiros a alterar** (9 serviços):
- `services/project_scope_sync_service.py`
- `services/project_status_sync_service.py`
- `services/project_decisions_sync_service.py`
- `services/project_risks_sync_service.py`
- `services/project_deliveries_sync_service.py`
- `services/project_requirements_sync_service.py`
- `services/project_plan_sync_service.py`
- `services/project_budget_sync_service.py`
- `services/project_mirror_sync_service.py`

**Padrão a aplicar em cada serviço**:

**4a) No `__init__`** — remover `self.publisher = GitHubRepositoryPublisher(env)`.

**4b) Adicionar método `_build_publisher`**:
```python
def _build_publisher(self, project):
    """Build a publisher scoped to this project's key (legacy mode if key is not set)."""
    project_key = project._pg_resolve_project_key()
    return GitHubRepositoryPublisher(self.env, project_key=project_key)
```

**4c) No `process_run` (ou equivalente)** — criar publisher no início do processamento do projeto:
```python
publisher = self._build_publisher(project)
```

E substituir todas as referências a `self.publisher` por `publisher` dentro desse scope.

**4d) `snapshot_path` no sync run** — usar a propriedade do publisher em vez do string hardcoded.

Em `project_scope_sync_service.py`, substituir:
```python
# ANTES:
'snapshot_path': '.pg/PG_SCOPE_SYNC.json',
# DEPOIS (publisher deve estar criado antes deste ponto):
'snapshot_path': publisher.scope_snapshot_path,
```

Aplicar o equivalente em cada serviço com o path correto:
| Serviço | Propriedade do publisher |
|---|---|
| `project_scope_sync_service.py` | `publisher.scope_snapshot_path` |
| `project_status_sync_service.py` | `publisher.status_snapshot_path` |
| `project_decisions_sync_service.py` | `publisher.decisions_snapshot_path` |
| `project_risks_sync_service.py` | `publisher.risks_snapshot_path` |
| `project_deliveries_sync_service.py` | `publisher.deliveries_snapshot_path` |
| `project_requirements_sync_service.py` | `publisher.requirements_snapshot_path` |
| `project_plan_sync_service.py` | `publisher.project_plan_snapshot_path` |
| `project_budget_sync_service.py` | `publisher.budget_snapshot_path` |
| `project_mirror_sync_service.py` | *(mirror não tem snapshot_path no run — ignorar)* |

**Atenção**: verificar se os serviços criam o run ANTES de terem o publisher disponível. Se sim, criar o publisher antes da criação do run:

```python
# Ordem correcta dentro de process_run:
publisher = self._build_publisher(project)  # 1. criar publisher
run = self.env['pg.project.scope.sync.run'].sudo().create({
    ...
    'snapshot_path': publisher.scope_snapshot_path,  # 2. usar path do publisher
    ...
})
```

Se o publisher precisar do projeto mas o projeto for passado ao `process_run` — verificar a assinatura real de `process_run` e adaptar.

**Check**: executar os testes existentes — nenhum deve quebrar em modo legacy (sem `pg_project_key`):
```bash
python -m pytest pg_brodoo/tests/test_sync_services.py -x -q
python -m pytest pg_brodoo/tests/test_payload_builders.py -x -q
```

---

### Passo 5 — Chamada a `update_project_index` após publish bem-sucedido

**Ficheiros**: `project_scope_sync_service.py` e `project_mirror_sync_service.py`

Após o publish do snapshot ter sucesso (antes de escrever o status final no run), chamar:

```python
# Em project_scope_sync_service.py — após publish bem-sucedido:
try:
    publisher.update_project_index(
        repository=project.pg_repository_id,
        branch_name=project.pg_repo_branch,
        project_id=project.id,
        project_key=project._pg_resolve_project_key(),
        project_name=project.name,
    )
except Exception:
    # Falha no índice não deve bloquear o sync principal
    _logger.warning('pg_brodoo: failed to update PG_PROJECT_INDEX.json for project %s', project.id, exc_info=True)
```

O `try/except` é obrigatório: uma falha a actualizar o índice não deve impedir o sync principal.

**Check**: se `project_key` for `None`, o método `update_project_index` retorna `None` sem chamar a API — verificar que não gera erro.

---

### Passo 6 — View: campo `pg_project_key` no formulário do projeto

**Ficheiro**: `pg_brodoo/views/project_project_views.xml`

Localizar o grupo que contém `pg_repository_id` e `pg_repo_branch` e adicionar:

```xml
<field name="pg_project_key"
       string="PG Project Key"
       placeholder="ex: alpha-crm (auto-derivado do nome se vazio)"
       attrs="{'readonly': [('pg_scope_sync_last_published_at', '!=', False)]}"/>
```

O campo fica editável enquanto `pg_scope_sync_last_published_at` for `False` (antes do primeiro sync). Após o primeiro publish de scope, passa a read-only.

**Alternativa se `attrs` não for suportado na view actual**: usar grupos separados ou `invisible`.

---

### Passo 7 — Testes novos

**Ficheiro**: `pg_brodoo/tests/test_sync_services.py` (ou ficheiro de teste específico)

Adicionar os seguintes testes:

```python
class TestProjectKeySlug(TransactionCase):
    def test_derive_project_key_basic(self):
        project = self.env['project.project'].new({'name': 'Alpha CRM'})
        self.assertEqual(project._pg_derive_project_key('Alpha CRM'), 'alpha-crm')

    def test_derive_project_key_special_chars(self):
        project = self.env['project.project'].new({'name': 'Alpha CRM - Fase 2!'})
        self.assertEqual(project._pg_derive_project_key('Alpha CRM - Fase 2!'), 'alpha-crm-fase-2')

    def test_derive_project_key_unicode(self):
        project = self.env['project.project'].new({'name': 'Projeto São João'})
        key = project._pg_derive_project_key('Projeto São João')
        self.assertRegex(key, r'^[a-z0-9][a-z0-9\-]*$')

    def test_derive_project_key_max_length(self):
        long_name = 'A' * 100
        key = project._pg_derive_project_key(long_name)
        self.assertLessEqual(len(key), 48)


class TestPublisherPaths(TransactionCase):
    def test_legacy_mode_scope_path(self):
        publisher = GitHubRepositoryPublisher(self.env, project_key=None)
        self.assertEqual(publisher.scope_snapshot_path, '.pg/PG_SCOPE_SYNC.json')

    def test_legacy_mode_context_path(self):
        publisher = GitHubRepositoryPublisher(self.env, project_key=None)
        self.assertEqual(publisher.project_context_path, 'PG_CONTEXT.md')

    def test_namespaced_scope_path(self):
        publisher = GitHubRepositoryPublisher(self.env, project_key='alpha-crm')
        self.assertEqual(publisher.scope_snapshot_path, '.pg/projects/alpha-crm/PG_SCOPE_SYNC.json')

    def test_namespaced_context_path(self):
        publisher = GitHubRepositoryPublisher(self.env, project_key='alpha-crm')
        self.assertEqual(publisher.project_context_path, 'projects/alpha-crm/PG_CONTEXT.md')

    def test_namespaced_mirror_tasks_path(self):
        publisher = GitHubRepositoryPublisher(self.env, project_key='alpha-crm')
        self.assertEqual(publisher._path('mirror_tasks'), '.pg/projects/alpha-crm/tasks/tasks.json')

    def test_empty_string_key_treated_as_legacy(self):
        publisher = GitHubRepositoryPublisher(self.env, project_key='')
        self.assertIsNone(publisher._project_key)
        self.assertEqual(publisher.scope_snapshot_path, '.pg/PG_SCOPE_SYNC.json')


class TestProjectKeyConstraints(TransactionCase):
    def test_invalid_format_raises(self):
        project = self.env['project.project'].create({'name': 'Test'})
        with self.assertRaises(ValidationError):
            project.write({'pg_project_key': 'Invalid Key!'})

    def test_valid_format_ok(self):
        project = self.env['project.project'].create({'name': 'Test'})
        project.write({'pg_project_key': 'valid-key-123'})
        self.assertEqual(project.pg_project_key, 'valid-key-123')

    def test_uniqueness_per_repo_branch(self):
        repo = self.env['pg.ai.repository'].create({
            'name': 'Test Repo', 'full_name': 'org/repo',
            'github_owner': 'org', 'github_repo': 'repo', 'default_branch': 'main',
        })
        project_a = self.env['project.project'].create({'name': 'Project A'})
        project_a.write({
            'pg_repository_id': repo.id,
            'pg_repo_branch': 'main',
            'pg_project_key': 'project-a',
        })
        project_b = self.env['project.project'].create({'name': 'Project B'})
        with self.assertRaises(ValidationError):
            project_b.write({
                'pg_repository_id': repo.id,
                'pg_repo_branch': 'main',
                'pg_project_key': 'project-a',  # colisão
            })
```

---

## Critérios de aceitação (checklist antes de fechar F1)

Todos os itens abaixo devem estar ✅ antes de considerar F1 concluído.

### Testes unitários
- [ ] `test_derive_project_key_*` todos a passar
- [ ] `test_legacy_mode_*` todos a passar (backward compat)
- [ ] `test_namespaced_*` todos a passar
- [ ] `test_invalid_format_raises` a passar
- [ ] `test_uniqueness_per_repo_branch` a passar
- [ ] Testes existentes (`test_sync_services.py`, `test_payload_builders.py`) sem regressões

### Verificações de código
- [ ] Nenhum `self.publisher = GitHubRepositoryPublisher(env)` sem `project_key` nos serviços
- [ ] Todas as referências às antigas constantes (`SCOPE_SNAPSHOT_PATH`, etc.) removidas do publisher
- [ ] `snapshot_path` em cada sync run usa a propriedade do publisher (não string hardcoded)
- [ ] `update_project_index` tem `try/except` no ponto de chamada

### Migração
- [ ] `__manifest__.py` tem versão `19.0.1.1.0`
- [ ] Pasta `migrations/19.0.1.1.0/` existe

### Backward compat
- [ ] Projeto sem `pg_project_key` → `publisher._project_key is None`
- [ ] Projeto sem `pg_project_key` → todos os paths são iguais aos actuais (nenhuma regressão)
- [ ] `update_project_index` com `project_key=None` → retorna `None` sem erro e sem chamada HTTP

### UI
- [ ] Campo `pg_project_key` visível no form do projeto junto de `pg_repository_id`
- [ ] Campo fica read-only após o primeiro publish de scope

---

## O que NÃO fazer nesta fase

- ❌ Não gerar `PG_CONTEXT.md` raiz como índice global (F2)
- ❌ Não mover artefactos existentes no GitHub (migração de dados — decisão separada)
- ❌ Não adicionar `pg_project_key` obrigatório nem com `required=True`
- ❌ Não alterar schemas JSON dos payloads (os sync payloads não mudam — só os paths)
- ❌ Não alterar `vendor/odoo_src` (read-only)
- ❌ Não fazer auto-assign de `pg_project_key` em `create()` sem input do operador

---

## Ficheiros a tocar — lista completa

| # | Ficheiro | Tipo |
|---|---|---|
| 1 | `pg_brodoo/__manifest__.py` | bump versão |
| 2 | `pg_brodoo/migrations/19.0.1.1.0/post-migrate.py` | novo |
| 3 | `pg_brodoo/models/project_project.py` | campo + métodos + constraints |
| 4 | `pg_brodoo/services/github_repository_publisher.py` | refactor completo |
| 5 | `pg_brodoo/services/project_scope_sync_service.py` | `_build_publisher` + index call |
| 6 | `pg_brodoo/services/project_status_sync_service.py` | `_build_publisher` |
| 7 | `pg_brodoo/services/project_decisions_sync_service.py` | `_build_publisher` |
| 8 | `pg_brodoo/services/project_risks_sync_service.py` | `_build_publisher` |
| 9 | `pg_brodoo/services/project_deliveries_sync_service.py` | `_build_publisher` |
| 10 | `pg_brodoo/services/project_requirements_sync_service.py` | `_build_publisher` |
| 11 | `pg_brodoo/services/project_plan_sync_service.py` | `_build_publisher` |
| 12 | `pg_brodoo/services/project_budget_sync_service.py` | `_build_publisher` |
| 13 | `pg_brodoo/services/project_mirror_sync_service.py` | `_build_publisher` + index call |
| 14 | `pg_brodoo/views/project_project_views.xml` | campo `pg_project_key` |
| 15 | `pg_brodoo/tests/test_sync_services.py` | novos testes (ou ficheiro novo) |

---

## Referências

- `docs/PG_005_ARCHITECTURE_CONTRACT.md` — contrato arquitetural completo
- `docs/PG_005_BRODOO_CHANGE_SPEC.md` — spec detalhada (origem deste handoff)
- `docs/PG_FRAMEWORK_IMPROVEMENT_BACKLOG.md` — contexto do backlog
