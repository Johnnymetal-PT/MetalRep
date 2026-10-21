from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    area_fiscal = fields.Char(string='Área Fiscal')
    ordem_da_sucursal = fields.Char(string='Ordem da Sucursal')
