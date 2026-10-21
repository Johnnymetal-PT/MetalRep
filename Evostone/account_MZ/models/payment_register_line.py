from odoo import models, fields, api


class PaymentRegisterLine(models.Model):
    _name = 'payment.register.line'
    _description = 'Linha do Registo de Pagamento'

    categoria = fields.Char(string='Categoria')
    employee_id = fields.Many2one('hr.employee', string='Funcionário')
    irps = fields.Float(string='IRPS')
    mr20_id = fields.Many2one('report.m20', string='Registo de Pagamento')
    nuit = fields.Char(string='Nuit')
    register_id = fields.Many2one('payment.register', string='Registo de Pagamento')
    rendimento = fields.Float(string='Rendimento Bruto')
