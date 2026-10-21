# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # =====================
    # CATEGORIA DA VARIANTE
    # =====================
    variant_categ_id = fields.Many2one(
        'product.category',
        string='Categoria da Variante',
        help='Se definido, esta categoria será usada em vez da categoria do template.',
    )

    categ_id = fields.Many2one(
        'product.category',
        string='Product Category',
        compute='_compute_categ_id',
        inverse='_inverse_categ_id',
        store=True,
        readonly=False,
    )

    @api.depends('variant_categ_id', 'product_tmpl_id.categ_id')
    def _compute_categ_id(self):
        for product in self:
            if product.variant_categ_id:
                product.categ_id = product.variant_categ_id
            elif product.product_tmpl_id:
                product.categ_id = product.product_tmpl_id.categ_id

    def _inverse_categ_id(self):
        for product in self:
            if product.product_tmpl_id and product.categ_id != product.product_tmpl_id.categ_id:
                product.variant_categ_id = product.categ_id
            else:
                product.variant_categ_id = False
