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
