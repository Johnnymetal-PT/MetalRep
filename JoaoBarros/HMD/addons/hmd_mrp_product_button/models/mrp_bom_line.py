# -*- coding: utf-8 -*-
from odoo import _, models


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

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
