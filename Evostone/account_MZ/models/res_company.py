from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    alvara = fields.Many2many('alvara.model', string='Alvarás')
