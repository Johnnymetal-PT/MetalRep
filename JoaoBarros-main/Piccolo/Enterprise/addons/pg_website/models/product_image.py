from odoo import models, fields, api

class ProductImage(models.Model):
    _inherit = 'product.image'

    image_base64 = fields.Char(
        compute='_compute_image_base64',
        store=True
    )

    @api.depends('image_1920')
    def _compute_image_base64(self):
        for image in self:
            if image.image_1920:
                image.image_base64 = image.image_1920.decode('utf-8')
            else:
                image.image_base64 = ''