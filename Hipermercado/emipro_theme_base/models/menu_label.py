# -*- coding: utf-8 -*-
"""Menu Label Module"""

from odoo import fields, models


class MenuLabel(models.Model):
    """
    This Class is used to handle menu label records
    """

    _name = "menu.label"
    _description = "Menu Label"

    name = fields.Char("Name", required=True, translate=True, help="Name of the menu label")
    label_background_color = fields.Char(string='Background Color',
                                         help="Here you can set a specific HTML color index (e.g. #ff0000) to display "
                                              "the menu label background color", default="#ff0000")
    label_text_color = fields.Char(string='Color',
                                   help="Here you can set a specific HTML color index (e.g. #ff0000) to display the "
                                        "text color of menu label.", default="#00ff00")
    category_ids = fields.One2many('product.public.category', 'menu_label_id', 'Category Ids')
