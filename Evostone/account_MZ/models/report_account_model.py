from odoo import models, fields


class ReportAccountModel(models.Model):
    _name = 'report.account.model'
    _description = 'Report Account'

    contas = fields.Many2many('account.account', 'report_account_rel', 'report_account_id', 'account_id', string='Contas')
    contas_excld = fields.Many2many('account.account', 'account_rel', 'report_id', 'account_id', string='Contas Excld')
    formula = fields.Selection([], string='Formula')
    name = fields.Char(string='Name')
