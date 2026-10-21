"""Campos auxiliares para homepage/listagem de produtos no website Essani."""
from odoo import models, fields, api
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    extra_image_ids = fields.One2many(
        'product.image',
        'product_tmpl_id',
        string='Extra Images',
        domain=[('product_variant_id', '=', False)]
    )

    main_image = fields.Binary(string='Main Image', compute='_compute_main_image')

    @api.depends('image_1920')
    def _compute_main_image(self):
        for record in self:
            record.main_image = record.image_1920
