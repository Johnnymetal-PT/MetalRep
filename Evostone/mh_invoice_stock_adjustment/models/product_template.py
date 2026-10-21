# -*- coding: utf-8 -*-

from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    acerto_de_stock = fields.Boolean(
        string='Acerto de Stock',
        default=False,
        help='Marcar para produtos de serviço usados como acerto de diferença entre recepção e facturação.',
    )
