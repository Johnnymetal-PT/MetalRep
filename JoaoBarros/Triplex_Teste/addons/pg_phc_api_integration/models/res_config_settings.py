# -*- coding: utf-8 -*-

from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    phc_username = fields.Char(
        related="company_id.phc_username", readonly=False, string="Username")
    phc_password = fields.Char(
        related="company_id.phc_password", readonly=False, string="Password")
