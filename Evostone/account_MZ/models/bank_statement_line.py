from odoo import models, fields, api


class BankStatementLine(models.Model):
    _name = 'bank.statement.line'
    _description = 'Bank Statement Line'

    account_bank_statement_line_id = fields.Many2one('account.bank.statement.line', string='Linha Contabilística')
    amount = fields.Monetary(string='Valor')
    company_id = fields.Many2one('res.company', string='Empresa')
    currency_id = fields.Many2one('res.currency', string='Moeda')
    date = fields.Date(string='Data')
    journal_id = fields.Many2one('account.journal', string='Diário')
    parent_state = fields.Selection([], string='Estado do Extracto')
    partner_id = fields.Many2one('res.partner', string='Parceiro')
    payment_ref = fields.Char(string='Referência')
    statement_id = fields.Many2one('bank.statement', string='Extracto')
