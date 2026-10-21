# -*- coding: utf-8 -*-
""" Inherit the product product model"""

import logging
import datetime

from odoo import fields, models
from odoo.http import request

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    """Inherit the product product model"""

    _inherit = "product.product"

    product_brand_id = fields.Many2one('product.brand', related='product_tmpl_id.product_brand_id')

    def remove_cart_button(self):
        return self.sudo().out_of_stock()

    def out_of_stock(self):
        stock = 0
        for product in self.product_variant_ids:
            stock += product.sudo().with_context(warehouse=request.website.warehouse_id.id).free_qty
        if self.type == 'consu' and self.is_storable == True and not self.allow_out_of_stock_order and stock < 1:
            return True
        return False

    def get_visitor_count(self):
        cutoff_date = fields.Datetime.now() - datetime.timedelta(days=request.website.top_sold_duration_days or 30)
        return self.env['website.track'].search_count([('visit_datetime', '>=', cutoff_date),
                                                       ('product_id', '=', self.id)]) or 0
