import logging

from odoo import _, fields
from odoo.exceptions import UserError

from .github_repository_publisher import GitHubRepositoryPublisher
from .project_effort_payload_builder import ProjectEffortPayloadBuilder

_logger = logging.getLogger(__name__)


class ProjectEffortSyncService:
    def __init__(self, env):
        self.env = env
        self.payload_builder = ProjectEffortPayloadBuilder(env)
        self._publisher_override = None

    @property
    def publisher(self):
        if self._publisher_override is None:
            self._publisher_override = GitHubRepositoryPublisher(self.env, project_key=None)
        return self._publisher_override

    def _build_publisher(self, project):
        project_key = project._pg_get_or_create_project_key()
        if not project_key and self._publisher_override is not None:
            return self._publisher_override
        return GitHubRepositoryPublisher(self.env, project_key=project_key)

    def _update_project_status(self, project, values):
        project.sudo().write(values)

    def sync_from_projects(self, projects, trigger_type, trigger_model, trigger_record_id=None):
        projects = projects.sudo().exists()
        runs = self.env['pg.project.effort.sync.run']
        for project in projects:
            run = self.queue_project(
                project,
                trigger_type=trigger_type,
                trigger_model=trigger_model,
                trigger_record_id=trigger_record_id or project.id,
            )
            if run and run.status == 'queued':
                # Trigger automático (create/write/unlink de timesheets): uma falha
                # na publicação para o GitHub não pode abortar a operação de negócio
                # de quem só quis registar horas. O savepoint protege a transação;
                # o run fica em 'error' para reprocessamento manual (botão Retry).
                try:
                    with self.env.cr.savepoint():
                        self.process_run(run)
                except Exception as exc:
                    _logger.exception(
                        "Effort sync falhou para o projeto %s (trigger %s); a operação de negócio continua.",
                        project.id, trigger_type,
                    )
                    run.sudo().write({
                        'status': 'error',
                        'message': str(exc),
                        'finished_at': fields.Datetime.now(),
                    })
                    self._update_project_status(project, {
                        'pg_effort_sync_last_status': 'error',
                        'pg_effort_sync_last_message': str(exc),
                    })
                runs |= run
        return runs

    def queue_project(self, project, trigger_type='manual_button', trigger_model='project.project', trigger_record_id=None):
        project = project.exists()
        if not project or not project.pg_effort_sync_enabled:
            return False
        if not project.pg_repository_id or not (project.pg_repo_branch or '').strip():
            return False

        existing_run = self.env['pg.project.effort.sync.run'].sudo().search(
            [('project_id', '=', project.id), ('status', 'in', ('queued', 'running'))],
            order='create_date asc, id asc',
            limit=1,
        )
        if existing_run:
            return existing_run

        publisher = self._build_publisher(project)
        run = self.env['pg.project.effort.sync.run'].sudo().create(
            {
                'project_id': project.id,
                'status': 'queued',
                'trigger_type': trigger_type,
                'trigger_model': trigger_model,
                'trigger_record_id': trigger_record_id or project.id,
                'snapshot_path': publisher.effort_snapshot_path,
                'message': _('Queued for project effort publication.'),
            }
        )
        self._update_project_status(
            project,
            {
                'pg_effort_sync_last_status': 'queued',
                'pg_effort_sync_last_message': _('Project effort sync queued.'),
            },
        )
        return run

    def process_run(self, run):
        run = run.sudo().exists()
        if not run:
            return False

        project = run.project_id.sudo().exists()
        if not project:
            run.write({'status': 'error', 'message': _('Project no longer exists.'), 'finished_at': fields.Datetime.now()})
            return False

        if not project.pg_repository_id or not (project.pg_repo_branch or '').strip():
            raise UserError(_("The project must define both a repository and a repository branch for effort sync."))
        publisher = self._build_publisher(project)

        # Governanca: a branch alvo tem de existir; no fluxo automatico sinalizamos
        # em vez de criar (criacao com escolha de base e feita via botao/wizard).
        if not publisher.github_service.branch_exists(project.pg_repository_id, project.pg_repo_branch):
            message = _(
                "A branch '%s' nao existe no repositorio. Abra o projeto e use "
                "'Sincronizar Agora' para a criar (escolhendo a branch base)."
            ) % project.pg_repo_branch
            run.write({'status': 'error', 'message': message, 'finished_at': fields.Datetime.now()})
            self._update_project_status(
                project,
                {
                    'pg_effort_sync_last_status': 'error',
                    'pg_effort_sync_last_message': message,
                },
            )
            return run

        run.write({'status': 'running', 'started_at': fields.Datetime.now(), 'message': _('Building payload.')})
        self._update_project_status(
            project,
            {'pg_effort_sync_last_status': 'running', 'pg_effort_sync_last_message': _('Building project effort payload.')},
        )

        try:
            payload = self.payload_builder.build_payload(
                project,
                trigger_type=run.trigger_type,
                trigger_model=run.trigger_model,
                trigger_record_id=run.trigger_record_id,
            )
            payload_hash = self.payload_builder.payload_hash(payload)
            payload['source_metadata']['payload_hash'] = payload_hash
            self.payload_builder.validate_payload(payload)
            run.write({'payload_hash': payload_hash})

            if project.pg_effort_sync_last_payload_hash == payload_hash:
                run.write({'status': 'skipped', 'message': _('Project effort snapshot unchanged; publication skipped.'), 'finished_at': fields.Datetime.now()})
                self._update_project_status(
                    project,
                    {
                        'pg_effort_sync_last_status': 'skipped',
                        'pg_effort_sync_last_message': _('Project effort snapshot unchanged; nothing to publish.'),
                    },
                )
                return run

            publish_result = publisher.publish_project_effort_snapshot(project.pg_repository_id, project.pg_repo_branch, payload)
            run.write(
                {
                    'status': 'done',
                    'message': _('Project effort snapshot published successfully.'),
                    'published_file_sha': (publish_result.get('content') or {}).get('sha') or '',
                    'published_commit_sha': (publish_result.get('commit') or {}).get('sha') or '',
                    'finished_at': fields.Datetime.now(),
                }
            )
            self._update_project_status(
                project,
                {
                    'pg_effort_sync_last_status': 'done',
                    'pg_effort_sync_last_payload_hash': payload_hash,
                    'pg_effort_sync_last_published_at': fields.Datetime.now(),
                    'pg_effort_sync_last_message': _('Project effort snapshot published to repository.'),
                },
            )
            return run
        except Exception as exc:
            _logger.exception("Project effort sync failed for run %s", run.id)
            run.write({'status': 'error', 'message': str(exc), 'finished_at': fields.Datetime.now()})
            self._update_project_status(project, {'pg_effort_sync_last_status': 'error', 'pg_effort_sync_last_message': str(exc)})
            raise
