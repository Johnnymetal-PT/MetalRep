from odoo import models, fields, api


class BankStatement(models.Model):
    _name = 'bank.statement'
    _description = 'Bank Statement'

    balance_end = fields.Monetary(string='Saldo Final Calculado', currency_field='currency_id')
    balance_end_real = fields.Monetary(string='Saldo Final Real', currency_field='currency_id')
    balance_start = fields.Monetary(string='Saldo Inicial', currency_field='currency_id')
    bank_statement_lines = fields.One2many('bank.statement.line', 'statement_id', string='Linhas do Extracto')
    company_id = fields.Many2one('res.company', string='Empresa')
    currency_id = fields.Many2one('res.currency', string='Moeda')
    date = fields.Date(string='Data')
    journal_id = fields.Many2one('account.journal', string='Diário')
    line_ids = fields.One2many('account.bank.statement.line', 'bank_statement_id', string='Linhas')
    name = fields.Char(string='Referência')
    state = fields.Selection([('draft', 'Rascunho'), ('posted', 'Publicado')], string='Estado', default='draft')

    # Methods for views
    def post_statement(self):
        """Post the bank statement"""
        for rec in self:
            rec.state = 'posted'
        return True

    def action_open_bank_reconcile_widget(self):
        """Open bank reconciliation widget"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reconciliação Bancária',
            'res_model': 'account.bank.statement.line',
            'view_mode': 'list,form',
            'domain': [('statement_id', '=', self.id)],
        }
