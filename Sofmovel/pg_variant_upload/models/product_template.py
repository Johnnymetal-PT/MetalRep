"""Heranca de `product.template` para expor `custom_attribute_ids`.

Pertence ao modulo `pg_variant_upload`. Permite mostrar na vista do produto a
lista de atributos textuais associados (ver `custom.product.attribute`).
"""
from odoo import models, fields

class ProductTemplate(models.Model):
    """Adiciona o One2many para os custom attributes do produto."""

    _inherit = 'product.template'

    # Relacao para atributos textuais criados pelo importador de variantes.
    custom_attribute_ids = fields.One2many('custom.product.attribute', 'product_id', string='Custom Attributes')
