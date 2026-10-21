from odoo import api, models

from ..services.project_effort_sync_service import ProjectEffortSyncService


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    def _get_pg_effort_sync_service(self):
        return ProjectEffortSyncService(self.env)

    def _pg_effort_target_projects(self):
        return self.mapped('project_id').exists()

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        if not self.env.context.get('pg_skip_effort_sync_enqueue'):
            self._get_pg_effort_sync_service().sync_from_projects(
                lines._pg_effort_target_projects(),
                trigger_type='timesheet_create',
                trigger_model='account.analytic.line',
                trigger_record_id=lines[:1].id or False,
            )
        return lines

    def write(self, vals):
        projects_before = self._pg_effort_target_projects()
        result = super().write(vals)
        if not self.env.context.get('pg_skip_effort_sync_enqueue'):
            projects_after = self._pg_effort_target_projects()
            projects = (projects_before | projects_after).exists()
            self._get_pg_effort_sync_service().sync_from_projects(
                projects,
                trigger_type='timesheet_write',
                trigger_model='account.analytic.line',
                trigger_record_id=self[:1].id or False,
            )
        return result

    def unlink(self):
        projects = self._pg_effort_target_projects()
        trigger_record_id = self[:1].id or False
        result = super().unlink()
        if not self.env.context.get('pg_skip_effort_sync_enqueue'):
            self._get_pg_effort_sync_service().sync_from_projects(
                projects,
                trigger_type='timesheet_unlink',
                trigger_model='account.analytic.line',
                trigger_record_id=trigger_record_id,
            )
        return result
