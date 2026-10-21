"""Atributos textuais descritivos do produto (alem dos atributos standard).

Cada produto pode ter varios ``custom.product.attribute`` (com
sequence). Sao usados pelo Excel de import para guardar descricoes
nao-variantes ("Texto sobre o material", "Cuidados de limpeza"...).
Modelo standard ``product.attribute`` so suporta valores discretos.
"""
from odoo import models, fields, api


class CustomProductAttribute(models.Model):
    _name = 'custom.product.attribute'
    _description = 'Custom Product Attribute'

    name = fields.Char('Attribute Name', required=True)
    product_id = fields.Many2one('product.template', string='Product', required=True)
    # description preenchido pelo import (textual da linha do Excel);
    # readonly para evitar overrides manuais que o re-import sobrescreve.
    description = fields.Char('Description', required=True, readonly=True)
    sequence = fields.Integer('Sequence', default=1)
    value_ids = fields.One2many('custom.product.attribute.value', 'attribute_id', string='Values')


class CustomProductAttributeValue(models.Model):
    _name = 'custom.product.attribute.value'
    _description = 'Custom Product Attribute Value'

    name = fields.Char('Variant Name', required=True)
    attribute_id = fields.Many2one('custom.product.attribute', string='Attribute', required=True)
    price = fields.Float('Price')


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    custom_attribute_ids = fields.One2many('custom.product.attribute', 'product_id', string='Custom Attributes')
