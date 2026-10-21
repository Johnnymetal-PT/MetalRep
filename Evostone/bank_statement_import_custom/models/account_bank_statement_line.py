from odoo import models, fields, api, _


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'
    
    # Não vamos mais sobrescrever action_new_line
    # pois vamos interceptar diretamente o botão de upload na view de importação