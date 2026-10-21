# -*- coding: utf-8 -*-
"""Product Attribute"""

from odoo import fields, models, api


class ProductAttribute(models.Model):
    """
        Inheritance of product attributes.

        Adds icon style, attribute popup link, and a range
        display type option with variant control.
    """

    _inherit = "product.attribute"

    icon_style = fields.Selection([('round', "Round"), ('square', "Square")], string="Icon Style",
                                  default='round', help="Here, Icon size is 40*40")
    attribute_popup_id = fields.Many2one('attribute.popup', string='Attribute popup',
                                         help='Show attribute popup on product page')
    display_type = fields.Selection(selection_add=[('range', 'Range')], ondelete={'range': 'set default'})

    @api.onchange('display_type')
    def _onchange_display_type(self):
        for attribute in self:
            if attribute.display_type == 'range':
                attribute.create_variant = 'no_variant'
