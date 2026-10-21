# -*- coding: utf-8 -*-
"""Price List Item Module"""

from odoo import fields, models


class PriceListItem(models.Model):
    """Inherit Price List Item Model to add offer message and timer display fields."""

    _inherit = "product.pricelist.item"

    offer_msg = fields.Text(string="Offer Message", translate=True, help="To set the message in offer timer.", size=35)
    is_display_timer = fields.Boolean(string='Show Offer Timer', help="It shows the offer timer on the product page.")
