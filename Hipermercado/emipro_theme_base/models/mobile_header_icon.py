# -*- coding: utf-8 -*-
"""Mobile Header Icon Module"""

from odoo import fields, models


class MobileHeaderIcon(models.Model):
    """
        Model to manage icons displayed in the mobile header of the website.
    """

    _name = "mobile.header.icon"
    _description = 'Mobile Header Icon'
    _order = "sequence, id"

    name = fields.Char(string="Header Icon Name", help="Name of Icon", required=True)
    sequence = fields.Integer('Sequence')
    link_url = fields.Char(string="Link URL", required=True, default='')
    header_icon = fields.Binary(string="Mobile Header Icon", required=True,
                                help="Upload a white-colored SVG icon for best visibility.")
    is_dynamic_option = fields.Boolean(string="Is Dynamic Option")
    dynamic_opt_type = fields.Selection([('search_opt', 'Search Sidebar'), ('categories_opt', 'Categories List')],
                                        string='Select Any Option')
