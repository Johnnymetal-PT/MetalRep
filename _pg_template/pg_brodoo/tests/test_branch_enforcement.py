from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

from ..services.github_service import GitHubService
from ..services.project_mirror_sync_service import ProjectMirrorSyncService
from .common import PgAiDevAssistantTestMixin


@tagged('post_install', '-at_install')
class TestBranchEnforcement(PgAiDevAssistantTestMixin, TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_pg_base_url()
        cls.repository = cls.create_repository(name='branch_guard_repo')
        cls.base_branch = cls.create_repository_branch(cls.repository, name='teste', is_default=True)
        cls.project = cls.create_project(cls.repository, name='Projeto Branch Guard')

    def test_project_defaults_repo_branch_to_brodoo(self):
        project = self.env['project.project'].with_context(
            pg_skip_scope_sync_enqueue=True,
            pg_skip_mirror_sync_enqueue=True,
        ).create({
            'name': 'Projeto sem branch explicita',
            'pg_repository_id': self.repository.id,
        })
        self.assertEqual(project.pg_repo_branch, 'brodoo')

    def test_project_without_repository_creates_without_branch(self):
        # Regressao: um projeto simples (sem repositorio) tem de ser criado sem
        # disparar as constraints de sync. A branch nao pode ser assumida quando
        # nao ha repositorio (com pg_effort_sync_enabled default=True, uma branch
        # sozinha violava a constraint effort).
        project = self.env['project.project'].create({'name': 'Projeto simples sem repositorio'})
        self.assertFalse(project.pg_repository_id)
        self.assertFalse(project.pg_repo_branch)

    def test_manual_sync_returns_wizard_when_branch_missing(self):
        with patch.object(GitHubService, 'branch_exists', return_value=False):
            action = self.project.action_sync_project_mirror_now()
        self.assertEqual(action.get('res_model'), 'pg.branch.create.wizard')
        self.assertEqual(action.get('context', {}).get('default_target_branch'), self.project.pg_repo_branch)
        self.assertEqual(action.get('context', {}).get('default_repository_id'), self.repository.id)

    def test_automatic_mirror_run_errors_when_branch_missing(self):
        service = ProjectMirrorSyncService(self.env)
        run = service.queue_project(
            self.project,
            trigger_type='project_write',
            trigger_model='project.project',
            trigger_record_id=self.project.id,
        )
        with patch.object(GitHubService, 'branch_exists', return_value=False):
            processed = service.process_run(run)
        self.assertEqual(processed.status, 'error')
        self.assertIn('nao existe', processed.message)
        self.assertEqual(self.project.pg_mirror_sync_last_status, 'error')

    def test_wizard_creates_branch_from_chosen_base_and_resyncs(self):
        wizard = self.env['pg.branch.create.wizard'].create({
            'project_id': self.project.id,
            'repository_id': self.repository.id,
            'target_branch': 'brodoo',
            'base_branch_id': self.base_branch.id,
        })
        created = {}

        def _fake_create_branch(svc_self, repository, branch_name, base_branch=None):
            created['branch_name'] = branch_name
            created['base_branch'] = base_branch
            return {'ref': f'refs/heads/{branch_name}'}

        with patch.object(GitHubService, 'create_branch', _fake_create_branch), \
             patch.object(GitHubService, 'sync_repository_branches', return_value=self.repository.branch_ids), \
             patch.object(GitHubService, 'branch_exists', return_value=False):
            wizard.action_create_branch()

        self.assertEqual(created.get('branch_name'), 'brodoo')
        self.assertEqual(created.get('base_branch'), self.base_branch.name)
