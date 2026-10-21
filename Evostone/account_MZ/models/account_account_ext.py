from odoo import models, fields


class AccountAccount(models.Model):
    _inherit = 'account.account'

    conta_mae = fields.Many2one('account.account', string='Conta Mae')
    contas_filhos = fields.One2many('account.account', 'conta_mae', string='Contas Filhas')
    current_period_balance = fields.Float(string='Current Period Balance', compute='_compute_current_period_balance', store=False)
    is_custom = fields.Boolean(string='Is Custom')
    itemmoves = fields.One2many('account.move.line', 'account_id', string='Movimentos')
    period_balance = fields.Float(string='Period Balance')

    def _compute_current_period_balance(self):
        for rec in self:
            rec.current_period_balance = 0.0
