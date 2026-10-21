# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools.translate import html_translate

class ProductBrand(models.Model):
    """
    Product Brand Model
    ===================
    Represents product brands that can be linked to products.
    Supports website publishing, searchability, multi-website,
    brand images, and product count.
    """

    _name = 'as.product.brand'
    _inherit = ['website.multi.mixin', 'website.searchable.mixin', 'image.mixin']
    _description = 'Product Brands'
    _order = 'sequence, id'

    active = fields.Boolean(default=True)
    sequence = fields.Integer()
    logo = fields.Binary(string='Logo')
    set_image_mixin = fields.Boolean(compute='_get_logo', store=True)
    name = fields.Char(string='Name', translate=True, required=True)
    brand_description = fields.Text(string='Short Description', translate=True)
    description = fields.Html(string='Detail Description', translate=html_translate)
    brand_product_ids = fields.One2many('product.template', 'product_brand_id', string='Products')
    products_count = fields.Integer(string='Number of products', compute='_get_products_count')

    # Unique constraint for brand name
    _name_unique = models.Constraint(
        'unique (name)',
        'Brand name already exists!',
    )

    @api.depends('logo')
    def _get_logo(self):
        """Set main image from logo and enable image mixin."""
        for rec in self:
            rec.image_1920 = rec.logo
            rec.set_image_mixin = True

    @api.depends('brand_product_ids')
    def _get_products_count(self):
        """Compute number of products for each brand."""
        for rec in self:
            rec.products_count = len(rec.brand_product_ids)

    def as_brand_product(self):
        """Redirect to brand's product list view."""
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'domain': [['product_brand_id', '=', self.id]],
            'name': 'Products',
            'view_mode': 'kanban,list,form',
        }
