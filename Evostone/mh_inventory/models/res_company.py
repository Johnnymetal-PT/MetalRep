# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    stone_density = fields.Float(
        string='Densidade Padrão (kg/m³)',
        default=2700.0,
        digits=(10, 2),
        help='Densidade default para cálculo de peso de produtos dimensionais '
             '(block/slab/strip/tiles) quando o produto não tem densidade '
             'específica configurada. Valor da indústria: 2700 kg/m³.',
    )
