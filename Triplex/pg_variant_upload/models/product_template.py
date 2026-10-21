"""
Extensoes simples em product.template para integrar com o fluxo de importacao.

Modulo: pg_variant_upload.
Ficheiro: pg_variant_upload\models\product_template.py.
Modelo principal: product.template.
"""

from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    custom_attribute_ids = fields.One2many('custom.product.attribute', 'product_id', string='Custom Attributes')
