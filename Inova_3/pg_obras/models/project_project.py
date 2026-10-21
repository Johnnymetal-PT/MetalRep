from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProjectProject(models.Model):
    _inherit = 'project.project'

    x_localizacao_projeto = fields.Many2one(
        comodel_name='stock.location',
        string="Localização do Projeto",
        copy=False,
        readonly=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        projects = super().create(vals_list)
        for project in projects:
            project._create_project_location_if_needed()
        return projects

    def write(self, vals):
        pre_partner = {p.id: p.partner_id for p in self}
        res = super().write(vals)
        # Se foi atribuído cliente ao projeto pela primeira vez -> criar localização
        if 'partner_id' in vals:
            for project in self:
                if not pre_partner.get(project.id) and project.partner_id:
                    project._create_project_location_if_needed()
        return res

    def _create_project_location_if_needed(self):
        for project in self:
            if project.x_localizacao_projeto:
                continue

            partner = project.partner_id
            if not partner:
                continue

            if not partner.x_localizacao_obra:
                partner._create_obra_location_if_needed()

            if not partner.x_localizacao_obra:
                raise UserError(_('O cliente não tem Localização da Obra definida.'))

            obra_location = partner.x_localizacao_obra
            company_id = project.company_id.id or partner.company_id.id or self.env.company.id

            existing = self.env['stock.location'].search([
                ('location_id', '=', obra_location.id),
                ('name', '=', project.name or _('Projeto')),
                ('company_id', '=', company_id),
            ], limit=1)

            if existing:
                project.x_localizacao_projeto = existing.id
                continue

            vals = {
                'name': project.name or _('Projeto'),
                'usage': obra_location.usage,
                'location_id': obra_location.id,
                'company_id': company_id,
            }
            loc = self.env['stock.location'].create(vals)
            project.x_localizacao_projeto = loc.id
