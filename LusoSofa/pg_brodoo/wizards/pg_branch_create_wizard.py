from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..services.github_service import GitHubService


class PgBranchCreateWizard(models.TransientModel):
    _name = 'pg.branch.create.wizard'
    _description = 'PG Criar Branch em Falta'

    project_id = fields.Many2one('project.project', string='Projeto', required=True)
    repository_id = fields.Many2one('pg.ai.repository', string='Repositorio', required=True)
    target_branch = fields.Char(string='Branch a criar', required=True, readonly=True)
    base_branch_id = fields.Many2one(
        'pg.ai.repository.branch',
        string='Copiar a partir de',
        required=True,
        domain="[('repository_id', '=', repository_id)]",
        help='Branch existente que serve de base (copia) para criar a nova branch.',
    )

    def _github_service(self):
        return GitHubService(self.env)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        repo_id = res.get('repository_id') or self.env.context.get('default_repository_id')
        if repo_id:
            repository = self.env['pg.ai.repository'].browse(repo_id)
            # Sincronizar as branches reais do repo para oferecer bases validas.
            self._github_service().sync_repository_branches(repository)
            if 'base_branch_id' in fields_list and not res.get('base_branch_id'):
                default_record = repository.get_default_branch_record()
                if default_record:
                    res['base_branch_id'] = default_record.id
        return res

    def action_create_branch(self):
        self.ensure_one()
        if not self.base_branch_id:
            raise UserError(_('Escolha a branch base a partir da qual copiar.'))
        github_service = self._github_service()
        if github_service.branch_exists(self.repository_id, self.target_branch):
            raise UserError(_("A branch '%s' ja existe no repositorio.") % self.target_branch)
        github_service.create_branch(
            self.repository_id,
            self.target_branch,
            base_branch=self.base_branch_id.name,
        )
        github_service.sync_repository_branches(self.repository_id)
        # A branch existe agora - re-disparar o sync do espelho.
        return self.project_id.action_sync_project_mirror_now()
