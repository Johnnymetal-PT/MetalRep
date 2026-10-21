from odoo import models, fields, api


class ProductCategory(models.Model):
    _inherit = 'product.category'
    
    # Campos para contas externas
    property_account_external_income_categ_id = fields.Many2one(
        'account.account',
        company_dependent=True,
        string="Conta de Rendimentos Externos",
        domain="[('deprecated', '=', False), ('account_type', 'not in', ('asset_receivable', 'liability_payable', 'asset_cash', 'liability_credit_card', 'off_balance'))]",
        help="Esta conta será usada para rendimentos externos desta categoria de produtos."
    )
    
    property_account_external_expense_categ_id = fields.Many2one(
        'account.account',
        company_dependent=True,
        string="Conta de Gastos Externos", 
        domain="[('deprecated', '=', False), ('account_type', 'not in', ('asset_receivable', 'liability_payable', 'asset_cash', 'liability_credit_card', 'off_balance'))]",
        help="Esta conta será usada para gastos externos desta categoria de produtos."
    )