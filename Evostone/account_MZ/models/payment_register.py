from odoo import models, fields


class PaymentRegister(models.Model):
    _name = 'payment.register'
    _description = 'Registo de Pagamentos'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    company = fields.Many2one('res.company', string='Empresa')
    date = fields.Date(string='Data')
    line_ids = fields.One2many('payment.register.line', 'register_id', string='Linhas de Pagamento')
    month_name = fields.Selection([
        ('1', 'Janeiro'), ('2', 'Fevereiro'), ('3', 'Março'),
        ('4', 'Abril'), ('5', 'Maio'), ('6', 'Junho'),
        ('7', 'Julho'), ('8', 'Agosto'), ('9', 'Setembro'),
        ('10', 'Outubro'), ('11', 'Novembro'), ('12', 'Dezembro'),
    ], string='Mês')
    name = fields.Char(string='Descrição')
    totalirps = fields.Float(string='Total de IRPS')
