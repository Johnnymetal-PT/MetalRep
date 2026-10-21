from odoo import models, fields


class DestinationAccount14Model(models.Model):
    _name = 'destination.account14.model'
    _description = 'destination.account14.model'

    name = fields.Char(string='Name')
    account = fields.Many2one('account.account', string='Account')
    amount = fields.Float(string='Saldo')
    percentagem = fields.Float(string='Percentagem')
    apuramento_id = fields.Many2one('apuramento.model', string='Apuramento')
    apuramento_temp_id = fields.Many2one('apuramento.template.model', string='Apuramento Temp')
