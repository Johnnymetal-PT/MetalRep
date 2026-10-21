# -*- coding: utf-8 -*-
"""Attribute Popup Model"""

from odoo import fields, models


class ProductMeasure(models.Model):
    """
    Model for attribute popup content.

    Stores a translatable name, HTML content, and a style
    option (popup or sidebar) to control how product
    attribute information is displayed on the website.
    """

    _name = "attribute.popup"
    _description = "Attribute Measure"

    name = fields.Char(string="Name", required=True, translate=True)
    content = fields.Html(string="Content", sanitize_overridable=True, translate=True)
    style = fields.Selection([('popup', "Popup"), ('sidebar', "Sidebar")], string="Content Style",
                             default='sidebar', help="Select style of content to render")
