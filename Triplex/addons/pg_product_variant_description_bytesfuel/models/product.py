# -*- coding: utf-8 -*-
from odoo.http import request
from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)

class ProductProduct(models.Model):
    _inherit = 'product.product'

    # Mark the field as translatable
    product_variant_desc = fields.Text(string='Variant Description', translate=True)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # Related field will inherit the translation capabilities
    product_variant_desc = fields.Text(related='product_id.product_variant_desc', string="Variant Description", readonly=True)

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    # Related field will inherit the translation capabilities
    product_variant_desc = fields.Text(
        related='product_id.product_variant_desc', 
        string="Variant Description", 
        readonly=True
    )

