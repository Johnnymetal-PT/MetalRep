# -*- coding: utf-8 -*-
from odoo import fields, models


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    product_form = fields.Selection(
        related='product_id.product_form',
        string='Forma do Produto',
        store=True,
        readonly=True,
    )

    def action_view_inventory(self):
        """Ajuste de inventário só mostra produtos sem Forma definida (não-pedras).

        As pedras (placas/slabs) têm product_form definido e são contadas
        por lote/slab, não pelo ajuste de inventário padrão.
        """
        action = super().action_view_inventory()
        domain = action.get('domain') or []
        domain = list(domain) + [('product_form', '=', 'none')]
        action['domain'] = domain
        return action
