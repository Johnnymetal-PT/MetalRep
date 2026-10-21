"""Helper para servir ``product.image.image_1920`` como string base64.

Usado em templates QWeb que injetam src="data:image/...;base64,{{...}}"
e nao querem aplicar conversao no template.
"""
from odoo import models, fields, api


class ProductImage(models.Model):
    _inherit = 'product.image'

    # store=True para ficar pesquisavel/consultavel rapidamente - tem
    # custo de espaco em BD; avaliar se ha muitas imagens.
    image_base64 = fields.Char(
        compute='_compute_image_base64',
        store=True,
    )

    @api.depends('image_1920')
    def _compute_image_base64(self):
        for image in self:
            if image.image_1920:
                # image_1920 e bytes; decode utf-8 da a string base64 crua.
                image.image_base64 = image.image_1920.decode('utf-8')
            else:
                image.image_base64 = ''
