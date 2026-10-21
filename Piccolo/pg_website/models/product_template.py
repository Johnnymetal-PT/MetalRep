"""Helpers de imagem em ``product.template`` para uso em QWeb.

- ``extra_image_ids`` expoe explicitamente o One2many de imagens extra
  para iteracao em templates do website.
- ``main_image`` e um espelho computed de ``image_1920`` para evitar
  ter de tratar fallback no QWeb.
"""
from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Identico ao One2many standard mas declarado explicitamente para
    # facilitar a leitura em templates QWeb deste modulo.
    extra_image_ids = fields.One2many(
        'product.image',
        'product_tmpl_id',
        string='Extra Images',
    )

    main_image = fields.Binary(string='Main Image', compute='_compute_main_image')

    @api.depends('image_1920')
    def _compute_main_image(self):
        for record in self:
            record.main_image = record.image_1920
