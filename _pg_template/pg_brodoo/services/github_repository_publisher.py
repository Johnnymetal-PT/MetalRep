import json
from datetime import datetime, timezone

from .github_service import GitHubService


class GitHubRepositoryPublisher:
    # Paths legacy — usados quando project_key é None (backward compat)
    _LEGACY = {
        'scope': '.pg/PG_SCOPE_SYNC.json',
        'effort': '.pg/PG_EFFORT_SYNC.json',
        'mirror_project': '.pg/project/project.json',
        'mirror_odoo_env': '.pg/project/odoo_env.json',
        'mirror_deliverables': '.pg/project/deliverables.json',
        'mirror_planning': '.pg/planning/planning.json',
        'mirror_tasks': '.pg/tasks/tasks.json',
        'mirror_chatter': '.pg/chatter/chatter.json',
        'mirror_attachments': '.pg/attachments/attachments.json',
        'mirror_history': '.pg/history/events.jsonl',
        'context': 'PG_CONTEXT.md',
    }

    _SNAPSHOT_FILES = {
        'scope': 'PG_SCOPE_SYNC.json',
        'effort': 'PG_EFFORT_SYNC.json',
    }

    _MIRROR_SUBPATHS = {
        'mirror_project': 'project/project.json',
        'mirror_odoo_env': 'project/odoo_env.json',
        'mirror_deliverables': 'project/deliverables.json',
        'mirror_planning': 'planning/planning.json',
        'mirror_tasks': 'tasks/tasks.json',
        'mirror_chatter': 'chatter/chatter.json',
        'mirror_attachments': 'attachments/attachments.json',
        'mirror_history': 'history/events.jsonl',
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
            return f".pg/projects/{self._project_key}/{self._SNAPSHOT_FILES[artifact_key]}"
        if artifact_key in self._MIRROR_SUBPATHS:
            return f".pg/projects/{self._project_key}/{self._MIRROR_SUBPATHS[artifact_key]}"
        if artifact_key == 'context':
            return f"projects/{self._project_key}/PG_CONTEXT.md"
        raise ValueError(f'Unknown artifact key: {artifact_key}')

    @property
    def scope_snapshot_path(self):
        return self._path('scope')

    @property
    def effort_snapshot_path(self):
        return self._path('effort')

    @property
    def project_context_path(self):
        return self._path('context')

    def _publish_snapshot(self, repository, snapshot_path, branch_name, payload, commit_message):
        content = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + '\n'
        return self.github_service.upsert_repository_file(
            repository,
            snapshot_path,
            content,
            commit_message,
            branch=branch_name,
        )

    def _publish_text_file(self, repository, snapshot_path, branch_name, content, commit_message):
        return self.github_service.upsert_repository_file(
            repository,
            snapshot_path,
            content,
            commit_message,
            branch=branch_name,
        )

    def publish_project_scope_snapshot(self, repository, branch_name, payload):
        return self._publish_snapshot(
            repository, self._path('scope'), branch_name, payload,
            'chore(pg-sync): refresh project scope from odoo',
        )

    def publish_project_effort_snapshot(self, repository, branch_name, payload):
        return self._publish_snapshot(
            repository, self._path('effort'), branch_name, payload,
            'chore(pg-sync): refresh project effort from odoo',
        )

    def publish_project_mirror_payload(self, repository, branch_name, payload):
        return self._publish_snapshot(
            repository, self._path('mirror_project'), branch_name, payload,
            'chore(pg-mirror): refresh project context from odoo',
        )

    def publish_odoo_env_payload(self, repository, branch_name, payload):
        return self._publish_snapshot(
            repository, self._path('mirror_odoo_env'), branch_name, payload,
            'chore(pg-mirror): refresh odoo environment from odoo',
        )

    def publish_deliverables_payload(self, repository, branch_name, payload):
        return self._publish_snapshot(
            repository, self._path('mirror_deliverables'), branch_name, payload,
            'chore(pg-mirror): refresh deliverables commitment from odoo',
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
        history_path = self._path('mirror_history')
        existing_content = self.github_service.get_repository_file_text(
            repository, history_path, branch=branch_name,
        )
        event_line = json.dumps(payload, ensure_ascii=False, sort_keys=True) + '\n'
        if existing_content:
            content = existing_content
            if not content.endswith('\n'):
                content += '\n'
            content += event_line
        else:
            content = event_line
        return self._publish_text_file(
            repository, history_path, branch_name, content,
            'chore(pg-mirror): append project history event from odoo',
        )

    def publish_project_context(self, repository, branch_name, content):
        return self._publish_text_file(
            repository, self._path('context'), branch_name, content,
            'chore(pg-mirror): refresh PG_CONTEXT from mirror artifacts',
        )

    def update_project_index(self, repository, branch_name, project_id, project_key, project_name, odoo_source=None):
        """
        Upsert this project in .pg/PG_PROJECT_INDEX.json.
        Called after the first successful publish of a namespaced project.
        Does nothing in legacy mode (no project_key).
        """
        if not self._project_key:
            return None

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
        content = json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + '\n'
        return self.github_service.upsert_repository_file(
            repository, self.PROJECT_INDEX_PATH, content,
            'chore(pg-sync): update project registry index',
            branch=branch_name,
        )
