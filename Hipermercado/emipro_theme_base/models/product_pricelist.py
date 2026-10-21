# -*- coding: utf-8 -*-
""" Inherit the product pricelist model"""

from odoo import fields, models


class PriceList(models.Model):
    """ Inherit the product pricelist model"""

    _inherit = "product.pricelist"

    enable_price_table = fields.Boolean('Price Table?',
                                        help='Display Price table for more '
                                             'than one minimum quantity rule')
