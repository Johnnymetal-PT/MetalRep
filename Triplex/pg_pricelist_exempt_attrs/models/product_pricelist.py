# -*- coding: utf-8 -*-
"""Campo da lista de preços com os atributos que ficam fora do acréscimo da lista."""
from odoo import fields, models


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    pg_exempt_attribute_ids = fields.Many2many(
        'product.attribute',
        'pg_pricelist_exempt_attr_rel', 'pricelist_id', 'attribute_id',
        string='Atributos sem acréscimo da lista',
        help="Os suplementos de preço (price extra) destes atributos não entram no cálculo "
             "da regra da lista: são somados ao preço depois de a regra ser aplicada.",
    )
