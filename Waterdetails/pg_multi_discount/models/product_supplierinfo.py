from odoo import fields, models


class ProductSupplierinfo(models.Model):
    _inherit = "product.supplierinfo"

    sh_multi_discount = fields.Char(string="Multi Discount %")
    sh_discount_amount = fields.Float(string="Discounted Unit Value", digits='Product Price')
    sh_discount_price_unit = fields.Float(string="Unit Total", digits='Product Price')
    sh_discounted_total_amount = fields.Float(string="Total Discounted Value", digits='Product Price')
