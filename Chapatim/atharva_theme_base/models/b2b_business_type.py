# -*- coding: utf-8 -*-

from odoo import models, fields

class BusinessType(models.Model):
    _name = 'b2b.business.type'
    _description = 'Business Type'

    name = fields.Char(string="Business Type", required=True)
    sequence = fields.Integer(string="Sequence", default=1)
