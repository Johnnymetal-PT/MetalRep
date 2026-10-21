from odoo import models, fields, api


class AccountCopyModel(models.Model):
    _name = 'account.copy.model'
    _description = 'Account Copy'

    account = fields.Many2one('account.account', string='Account')
    amount = fields.Float(string='Saldo')
    apuramento_id = fields.Many2one('apuramento.model', string='Apuramento')
    name = fields.Char(string='Name')
