from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Fields for the Consumption Table values, which are used in Manufacturing Orders
    price_1 = fields.Float(string="Price 1")
    price_2 = fields.Float(string="Price 2")
    price_3 = fields.Float(string="Price 3")
    price_4 = fields.Float(string="Price 4")
    price_5 = fields.Float(string="Price 5")
    price_6 = fields.Float(string="Price 6")
    price_7 = fields.Float(string="Price 7")
    price_8 = fields.Float(string="Price 8")
    price_9 = fields.Float(string="Price 9")
    price_10 = fields.Float(string="Price 10")

