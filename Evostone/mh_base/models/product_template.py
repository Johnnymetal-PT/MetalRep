# -*- coding: utf-8 -*-

from odoo import fields, models, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def action_view_stone_variants(self):
        """Abre a lista de variantes (product.product) deste template."""
        self.ensure_one()
        return {
            'name': _('Stone Variantes'),
            'type': 'ir.actions.act_window',
            'res_model': 'product.product',
            'view_mode': 'list,form',
            'views': [
                (self.env.ref('product.product_product_tree_view').id, 'list'),
                (False, 'form'),
            ],
            'domain': [('product_tmpl_id', '=', self.id)],
            'context': {
                'default_product_tmpl_id': self.id,
                'search_default_product_tmpl_id': self.id,
            },
        }
