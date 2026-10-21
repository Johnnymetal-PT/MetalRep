# -*- coding: utf-8 -*-
"""Product Brand Module"""

import re, unicodedata

from odoo import api, fields, models
from odoo.http import request
from odoo.tools.translate import html_translate


class ProductBrandEpt(models.Model):
    """
    Custom model to manage product brands in Odoo.    
    """

    _name = 'product.brand'
    _inherit = ['website.published.multi.mixin', 'image.mixin']
    _description = 'Product Brand'
    _order = 'sequence, name, id'

    name = fields.Char('Brand Name', required=True, translate=True)
    description = fields.Html('Description', sanitize_overridable=True, sanitize_attributes=False,
                              translate=html_translate, sanitize_form=False)
    website_id = fields.Many2one("website", string="Website")
    product_ids = fields.One2many('product.template', 'product_brand_id', string="Products", readonly=True)
    products_count = fields.Integer('Product Count', compute='_compute_products_count',
                                    help='Number of product counts that configured to brand')
    sequence = fields.Integer('Sequence', index=True, default=10)
    footer_description = fields.Html('Footer Description', sanitize_overridable=True, sanitize_attributes=False,
                                     translate=html_translate, sanitize_form=False)
    meta_title = fields.Text('Brand Meta Title', translate=True)
    meta_description = fields.Text('Brand Meta Description', translate=True)

    @api.depends('product_ids')
    def _compute_products_count(self):
        for brand in self:
            brand.products_count = len(brand.product_ids)

    def set_brand_wizard(self):
        return {'type': 'ir.actions.act_window',
                'res_model': 'product.brand.config',
                'name': "Product Configuration",
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_brand_id': self.id}}

    def get_product_count(self):
        domain = request.website.sale_product_domain()
        domain = domain + [('product_brand_id', '=', self.id)]
        count = request.env['product.template'].search_count(domain)
        return count

    def slugify(self, name=None):
        """
        Convert a brand name into a URL-safe slug.
        :param name:
        Returns:
            str: A clean, URL-friendly slug string.
        """
        text = name or self.name
        text = unicodedata.normalize('NFKD', text)
        text = text.replace('&', 'and').replace(' ', '-').replace("'", "")
        text = text.replace('.', '-')
        text = re.sub(r'-+', '-', text)
        text = re.sub(r'[^a-zA-Z0-9-]', '', text)
        return text.lower().strip('-')
