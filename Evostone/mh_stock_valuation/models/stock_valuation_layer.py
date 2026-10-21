# -*- coding: utf-8 -*-

from odoo import models, fields


class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    lot_group_id = fields.Many2one(
        'base.lot.group',
        string='Grupo de Lote',
        index=True,
        help="Grupo de lote associado a esta camada de valorização.",
    )
