from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    custom_attribute_ids = fields.One2many('custom.product.attribute', 'product_id', string='Custom Attributes')
