from odoo import models, fields

class ProductCategory(models.Model):
    _inherit = 'product.category'

    cat_image_1 = fields.Binary(string='Imagem 1', attachment=True)
    cat_image_2 = fields.Binary(string='Imagem 2', attachment=True)