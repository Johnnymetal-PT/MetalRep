from odoo import models, fields, api


class RendimentosModel(models.Model):
    _name = 'rendimentos.model'
    _description = 'Rendimentos'

    ano = fields.Integer(string='Ano')
    categoria = fields.Selection([], string='Categoria')
    contacto = fields.Many2one('res.partner', string='Contacto')
    is_company = fields.Selection([], string='Company Type')
    lancamento = fields.Many2one('account.move', string='Lançamento')
    mes = fields.Integer(string='Mês')
    morada = fields.Char(string='Morada')
    name = fields.Char(string='Name')
    nuit = fields.Char(string='Nuit')
    payslip = fields.Many2one('hr.payslip', string='Recibo de Vencimento')
    rendimento = fields.Float(string='Rendimento')
    retencao = fields.Float(string='Retençao')
    telefone = fields.Char(string='Telemovel')
