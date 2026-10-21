from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    deferred_expense_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Conta de Gastos Diferidos',
        related='product_tmpl_id.deferred_expense_account_id',
        readonly=False,
    )

    deferred_revenue_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Conta de Rendimentos Diferidos',
        related='product_tmpl_id.deferred_revenue_account_id',
        readonly=False,
    )
