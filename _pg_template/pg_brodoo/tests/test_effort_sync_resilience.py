from unittest.mock import Mock, patch

from odoo.tests import TransactionCase, tagged

from ..services import github_service as github_service_module
from ..services.github_service import GitHubApiError, GitHubService
from ..services.github_repository_publisher import GitHubRepositoryPublisher
from .common import PgAiDevAssistantTestMixin


@tagged('post_install', '-at_install')
class TestEffortSyncResilience(PgAiDevAssistantTestMixin, TransactionCase):
    """Regressões do incidente de 2026-07-10: falhas do publisher GitHub
    (sha obsoleto por escrita concorrente e erros transitórios 5xx) não podem
    abortar a operação de negócio de quem regista horas."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_pg_base_url()
        cls.repository = cls.create_repository(name='effort_resilience_repo')
        cls.project = cls.create_project(cls.repository, name='Projeto Effort Resilience')
        cls.employee = cls.env['hr.employee'].create(
            {
                'name': 'Empregado Effort',
                'user_id': cls.env.user.id,
            }
        )

    def test_timesheet_create_survives_publisher_failure(self):
        with patch.object(
            GitHubRepositoryPublisher,
            'publish_project_effort_snapshot',
            side_effect=GitHubApiError('GitHub API devolveu erro: Unicorn!', status_code=503),
        ):
            line = self.env['account.analytic.line'].create(
                {
                    'project_id': self.project.id,
                    'employee_id': self.employee.id,
                    'name': 'Registo de horas com publisher em baixo',
                    'unit_amount': 1.5,
                }
            )

        # A linha sobrevive à falha de publicação...
        self.assertTrue(line.exists())
        self.assertEqual(line.unit_amount, 1.5)

        # ...e o erro fica registado no run e no projeto para retry manual.
        run = self.env['pg.project.effort.sync.run'].search(
            [('project_id', '=', self.project.id)], order='id desc', limit=1
        )
        self.assertTrue(run)
        self.assertEqual(run.status, 'error')
        self.assertIn('Unicorn', run.message)
        self.assertEqual(self.project.pg_effort_sync_last_status, 'error')

    def test_upsert_retries_sha_conflict_with_refreshed_sha(self):
        service = GitHubService(self.env)
        put_payloads = []

        responses = [
            {'sha': 'sha-antigo', 'type': 'file'},   # GET inicial
            GitHubApiError(
                ".pg/projects/x/PG_EFFORT_SYNC.json does not match sha-antigo",
                status_code=409,
            ),                                        # PUT 1 -> conflito
            {'sha': 'sha-novo', 'type': 'file'},      # GET refrescado
            {'content': {'sha': 'sha-final'}, 'commit': {'sha': 'commit-final'}},  # PUT 2
        ]

        def _fake_request(method, endpoint, token=None, allow_not_found=False, **kwargs):
            result = responses.pop(0)
            if method == 'PUT':
                put_payloads.append(kwargs.get('json'))
            if isinstance(result, Exception):
                raise result
            return result

        with patch.object(GitHubService, '_request', side_effect=_fake_request), \
             patch.object(github_service_module.time, 'sleep', Mock()):
            result = service.upsert_repository_file(
                self.repository, '.pg/projects/x/PG_EFFORT_SYNC.json', '{}\n', 'chore: test', branch='teste'
            )

        self.assertEqual(result['commit']['sha'], 'commit-final')
        self.assertEqual(len(put_payloads), 2)
        self.assertEqual(put_payloads[0]['sha'], 'sha-antigo')
        # O retry tem de usar o sha refrescado, nunca repetir o obsoleto.
        self.assertEqual(put_payloads[1]['sha'], 'sha-novo')

    def test_upsert_does_not_retry_permanent_error(self):
        service = GitHubService(self.env)
        calls = []

        def _fake_request(method, endpoint, token=None, allow_not_found=False, **kwargs):
            calls.append(method)
            if method == 'GET':
                return {'sha': 'sha-atual', 'type': 'file'}
            raise GitHubApiError('Bad credentials', status_code=401)

        with patch.object(GitHubService, '_request', side_effect=_fake_request), \
             patch.object(github_service_module.time, 'sleep', Mock()):
            with self.assertRaises(GitHubApiError):
                service.upsert_repository_file(
                    self.repository, '.pg/PG_EFFORT_SYNC.json', '{}\n', 'chore: test', branch='teste'
                )

        # Erro permanente (401): sem retries — um único ciclo GET+PUT.
        self.assertEqual(calls, ['GET', 'PUT'])
