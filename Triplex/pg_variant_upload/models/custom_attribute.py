# -*- coding: utf-8 -*-
"""Atributos "personalizados" (descritivos, de texto) por produto, usados na importação.

Ao importar, valores de TEXTO das células do Excel são guardados aqui (em vez de como
variantes com preço). Ver o __manifest__.py.
"""
from odoo import models, fields

class CustomProductAttribute(models.Model):
    _name = 'custom.product.attribute'
    _description = 'Custom Product Attribute'

    name = fields.Char('Attribute Name', required=True)
    product_id = fields.Many2one('product.template', string='Product', required=True)
    description = fields.Char('Description', required=True)
    sequence = fields.Integer('Sequence', default=1)

class CustomProductAttributeValue(models.Model):
    _name = 'custom.product.attribute.value'
    _description = 'Custom Product Attribute Value'

    name = fields.Char('Variant Name', required=True)
    attribute_id = fields.Many2one('custom.product.attribute', string='Attribute', required=True)
    price = fields.Float('Price')
