from odoo import models, fields, api


class ReportM20(models.Model):
    _name = 'report.m20'
    _description = 'Report M20'

    ano = fields.Integer(string='Ano')
    company = fields.Many2one('res.company', string='Empresa')
    line_ids = fields.One2many('payment.register.line', 'mr20_id', string='Linhas de Pagamento')
    name = fields.Char(string='Name')
    nuit = fields.Char(string='Nuit da empresa')
    totalirps = fields.Float(string='Total de IRPS')
