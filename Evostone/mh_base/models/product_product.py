# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # Remover domain para mostrar todos os valores de atributos
    # Original: domain=[('attribute_line_id.value_count', '>', 1)]
    product_template_variant_value_ids = fields.Many2many(
        'product.template.attribute.value',
        relation='product_variant_combination',
        string="Variant Values",
        domain=[],  # Sem filtro - mostra todos
        ondelete='restrict'
    )
