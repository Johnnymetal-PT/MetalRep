from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    deferred_expense_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Conta de Gastos Diferidos',
        company_dependent=True,
        domain="[('deprecated', '=', False), "
               "('account_type', 'in', "
               "('asset_prepayments', 'asset_current', 'asset_non_current'))]",
        help="Conta específica de gastos diferidos para este produto. "
             "Se não preenchido, usa a conta default da empresa.",
    )

    deferred_revenue_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Conta de Rendimentos Diferidos',
        company_dependent=True,
        domain="[('deprecated', '=', False), "
               "('account_type', 'in', "
               "('liability_current', 'liability_non_current'))]",
        help="Conta específica de rendimentos diferidos para este produto. "
             "Se não preenchido, usa a conta default da empresa.",
    )
