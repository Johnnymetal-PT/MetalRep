# -*- coding: utf-8 -*-
""" Inherit the product public category model"""

from odoo import models, fields
from odoo.tools.translate import html_translate


class ProductPublicCategory(models.Model):
    """ Inherit the product public category model"""

    _inherit = "product.public.category"

    menu_label_id = fields.Many2one('menu.label', string='Menu Label', help='Select a menu label for this category')
    footer_description = fields.Html('Footer Description', sanitize_overridable=True, sanitize_attributes=False,
                                     translate=html_translate, sanitize_form=False)
