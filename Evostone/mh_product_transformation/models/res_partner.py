from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Boolean flags for partner type
    is_transformer = fields.Boolean(
        string='É Transformador',
        default=False,
        help='Indica se este parceiro é um transformador de produtos'
    )

    is_carrier = fields.Boolean(
        string='É Transportador',
        default=False,
        help='Indica se este parceiro é um transportador/carrier'
    )

    # Computed field for transformation count
    transformation_count = fields.Integer(
        string='Transformações',
        compute='_compute_transformation_count',
        help='Número de transformações realizadas por este parceiro'
    )

    @api.depends('is_transformer', 'is_carrier')
    def _compute_transformation_count(self):
        """Compute number of transformations for this partner"""
        TransformationDoc = self.env['transformation.document']
        for partner in self:
            count = 0
            if partner.is_transformer:
                count += TransformationDoc.search_count([
                    ('transformer_id', '=', partner.id)
                ])
            if partner.is_carrier:
                count += TransformationDoc.search_count([
                    ('carrier_id', '=', partner.id)
                ])
            partner.transformation_count = count

    def action_view_transformations(self):
        """Open transformations for this partner (when is_transformer or is_carrier)"""
        self.ensure_one()

        domain = []
        if self.is_transformer:
            domain.append(('transformer_id', '=', self.id))
        if self.is_carrier:
            if domain:
                domain = ['|'] + domain + [('carrier_id', '=', self.id)]
            else:
                domain = [('carrier_id', '=', self.id)]

        if not domain:
            domain = [('id', '=', False)]  # Empty domain

        return {
            'name': f'Transformações - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'transformation.document',
            'view_mode': 'list,form',
            'domain': domain,
            'context': {
                'default_transformer_id': self.id if self.is_transformer else False,
                'default_carrier_id': self.id if self.is_carrier else False,
            }
        }

    @api.constrains('is_transformer', 'is_carrier')
    def _check_transformer_carrier_exclusivity(self):
        """Ensure a partner can only be transformer OR carrier, not both"""
        for partner in self:
            if partner.is_transformer and partner.is_carrier:
                raise ValidationError(
                    _('❌ Um parceiro não pode ser Transformador E Transportador ao mesmo tempo!\n\n'
                      'Por favor, escolha apenas uma das opções.')
                )
