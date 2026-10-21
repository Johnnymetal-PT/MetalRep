# -*- coding: utf-8 -*-

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    phc_username = fields.Char(string="Username")
    phc_password = fields.Char(string="Password")
