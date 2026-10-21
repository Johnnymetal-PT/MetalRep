from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_tem_projeto = fields.Boolean(string="Tem Projeto")
    x_localizacao_obra = fields.Many2one(
        comodel_name='stock.location',
        string="Localização da Obra",
    )

    @api.model_create_multi
    def create(self, vals_list):
        partners = super().create(vals_list)
        for partner, vals in zip(partners, vals_list):
            if vals.get('x_tem_projeto'):
                partner._create_obra_location_if_needed()
        return partners

    def write(self, vals):
        pre_tem_projeto = {partner.id: partner.x_tem_projeto for partner in self}
        result = super().write(vals)
        if 'x_tem_projeto' in vals:
            for partner in self:
                was_tem_projeto = pre_tem_projeto.get(partner.id, False)
                if not was_tem_projeto and partner.x_tem_projeto:
                    partner._create_obra_location_if_needed()
        return result

    def _create_obra_location_if_needed(self):
        for partner in self:
            if partner.x_localizacao_obra:
                continue
            warehouse = partner._get_obras_warehouse()
            if not warehouse:
                raise UserError(_('O armazém Obras não foi encontrado.'))
            location_values = {
                'name': partner.name or _('Obra de parceiro'),
                'usage': warehouse.location_type,
                'location_id': warehouse.view_location_id.id,
                'company_id': partner.company_id.id or self.env.company.id,
            }
            partner.x_localizacao_obra = self.env['stock.location'].create(location_values)

    def _get_obras_warehouse(self):
        return self.env.ref('pg_obras.warehouse_obras', raise_if_not_found=False)
