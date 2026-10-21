# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    pcmp_price = fields.Float(
        string='PCMP Price',
        compute='_compute_pcmp_price',
        inverse='_set_pcmp_price',
        digits='Product Price',
        groups='base.group_user',
        help="Preço de Custo Médio Ponderado calculado por ano fiscal.",
    )

    @api.depends_context('company')
    @api.depends('product_variant_ids.pcmp_price')
    def _compute_pcmp_price(self):
        self._compute_template_field_from_variant_field('pcmp_price')

    def _set_pcmp_price(self):
        self._set_product_variant_field('pcmp_price')
