from odoo import models, fields, api

class CustomProductAttribute(models.Model):
    _name = 'custom.product.attribute'
    _description = 'Custom Product Attribute'

    name = fields.Char('Attribute Name', required=True)
    product_id = fields.Many2one('product.template', string='Product', required=True)
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


