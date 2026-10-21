# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class StockLocation(models.Model):
    _inherit = 'stock.location'

    is_consumption = fields.Boolean(
        string='Consumo Interno',
        default=False,
        help='Marque para usar esta localização como origem de consumo interno.',
    )

    @api.constrains('is_consumption', 'usage')
    def _check_unique_consumption_per_company(self):
        for loc in self:
            if not loc.is_consumption or loc.usage != 'internal':
                continue
            existing = self.search([
                ('is_consumption', '=', True),
                ('usage', '=', 'internal'),
                ('company_id', '=', loc.company_id.id),
                ('id', '!=', loc.id),
            ])
            if existing:
                raise ValidationError(_(
                    'Só pode existir uma localização interna de consumo por empresa.\n'
                    'Já existe: %s'
                ) % existing[0].display_name)
