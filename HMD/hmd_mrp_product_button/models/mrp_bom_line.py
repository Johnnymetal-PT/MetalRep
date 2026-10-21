# -*- coding: utf-8 -*-
"""Botao "Ver Produto" em `mrp.bom.line` e em `stock.move`.

Ambos partilham a mesma logica: abrir o `product.template` ligado ao
produto da linha. Usado nas listas de componentes da BoM, materia-prima
da MO e acabados da MO.

Ver `__manifest__.py` para o guia completo.
"""

from odoo import _, models


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    def action_view_product_template(self):
        """Abre o `product.template` do produto desta linha de BoM (no current)."""
        self.ensure_one()
        product = self.product_id
        if not product:
            return False
        template = product.product_tmpl_id
        if not template:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': _('Product Template'),
            'res_model': 'product.template',
            'view_mode': 'form',
            'res_id': template.id,
            'target': 'current',
        }
        
class StockMove(models.Model):
    _inherit = 'stock.move'

    def action_view_product_template(self):
        """Return an action that opens the related product template."""
        self.ensure_one()
        product = self.product_id
        if not product:
            return False
        template = product.product_tmpl_id
        if not template:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': _('Product Template'),
            'res_model': 'product.template',
            'view_mode': 'form',
            'res_id': template.id,
            'target': 'current',
        }
