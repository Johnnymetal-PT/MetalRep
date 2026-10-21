import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class PgProjectBatchRebuildArtifactsResult(models.TransientModel):
    _name = 'pg.project.batch.rebuild.artifacts.result'
    _description = 'Batch Rebuild Artifacts Result'

    wizard_id = fields.Many2one('pg.project.batch.rebuild.artifacts.wizard', ondelete='cascade')
    project_id = fields.Many2one('project.project', string='Projeto', readonly=True)
    status = fields.Selection(
        [('success', 'Sucesso'), ('error', 'Erro'), ('skipped', 'Ignorado')],
        string='Estado',
        readonly=True,
    )
    message = fields.Char(string='Mensagem', readonly=True)


class PgProjectBatchRebuildArtifactsWizard(models.TransientModel):
    _name = 'pg.project.batch.rebuild.artifacts.wizard'
    _description = 'Rebuild All Artifacts em Batch'

    state = fields.Selection([('confirm', 'Confirmacao'), ('done', 'Concluido')], default='confirm', readonly=True)

    eligible_project_ids = fields.Many2many(
        'project.project',
        'pg_batch_rebuild_artifacts_eligible_rel',
        'wizard_id',
        'project_id',
        string='Projetos Elegiveis',
        readonly=True,
    )
    ineligible_project_ids = fields.Many2many(
        'project.project',
        'pg_batch_rebuild_artifacts_ineligible_rel',
        'wizard_id',
        'project_id',
        string='Projetos Sem Repositorio/Branch',
        readonly=True,
    )
    eligible_count = fields.Integer(readonly=True)
    ineligible_count = fields.Integer(readonly=True)

    result_line_ids = fields.One2many(
        'pg.project.batch.rebuild.artifacts.result',
        'wizard_id',
        string='Resultados',
        readonly=True,
    )
    success_count = fields.Integer(readonly=True)
    error_count = fields.Integer(readonly=True)
    skipped_count = fields.Integer(readonly=True)

    @api.model
    def default_get(self, fields_list):
        vals = super().default_get(fields_list)
        project_ids = self.env.context.get('default_project_ids') or []
        if project_ids:
            projects = self.env['project.project'].browse(project_ids).exists()
            eligible = projects.filtered(lambda p: p.pg_repository_id and (p.pg_repo_branch or '').strip())
            ineligible = projects - eligible
            vals.update(
                {
                    'eligible_project_ids': [(6, 0, eligible.ids)],
                    'ineligible_project_ids': [(6, 0, ineligible.ids)],
                    'eligible_count': len(eligible),
                    'ineligible_count': len(ineligible),
                }
            )
        return vals

    def action_run_batch_rebuild(self):
        self.ensure_one()
        results = []
        success = error = skipped = 0

        for project in self.eligible_project_ids:
            try:
                service = project._get_pg_mirror_sync_service()
                run = service.queue_project(
                    project,
                    trigger_type='manual',
                    trigger_model='project.project',
                    trigger_record_id=project.id,
                    force_republish=True,
                )
                if run and run.status == 'queued':
                    service.process_run(run)
                    results.append(
                        {
                            'wizard_id': self.id,
                            'project_id': project.id,
                            'status': 'success',
                            'message': _('Rebuild All Artifacts publicado com sucesso.'),
                        }
                    )
                    success += 1
                elif run:
                    results.append(
                        {
                            'wizard_id': self.id,
                            'project_id': project.id,
                            'status': 'skipped',
                            'message': _('Sync ja em curso para este projeto.'),
                        }
                    )
                    skipped += 1
                else:
                    results.append(
                        {
                            'wizard_id': self.id,
                            'project_id': project.id,
                            'status': 'skipped',
                            'message': _('Mirror sync nao disponivel neste projeto.'),
                        }
                    )
                    skipped += 1
            except Exception as exc:
                _logger.exception('Erro no batch rebuild artifacts - projeto %s (id=%s)', project.name, project.id)
                results.append(
                    {
                        'wizard_id': self.id,
                        'project_id': project.id,
                        'status': 'error',
                        'message': str(exc)[:250],
                    }
                )
                error += 1

        for project in self.ineligible_project_ids:
            results.append(
                {
                    'wizard_id': self.id,
                    'project_id': project.id,
                    'status': 'skipped',
                    'message': _('Repositorio ou branch nao configurados.'),
                }
            )
            skipped += 1

        self.env['pg.project.batch.rebuild.artifacts.result'].create(results)
        self.write(
            {
                'state': 'done',
                'success_count': success,
                'error_count': error,
                'skipped_count': skipped,
            }
        )

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
