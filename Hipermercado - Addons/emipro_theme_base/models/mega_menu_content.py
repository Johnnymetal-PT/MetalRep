# -*- coding: utf-8 -*-
"""Mega Menu Content Module"""

from odoo import fields, models


class MegaMenuContent(models.Model):
    """
        Stores content items for website mega menus,
        including sequence, image, and optional URL.
    """

    _name = 'mega.menu.content'
    _order = ''
    _description = "Mega Menu Content"

    website_menu_id = fields.Many2one("website.menu", string="website menu", readonly=True)
    sequence = fields.Integer(string="Sequence")
    url = fields.Char(string="Image/Button URL", required=False)
    image = fields.Image("Image", required=False)
