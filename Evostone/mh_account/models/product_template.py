# -*- coding: utf-8 -*-
from odoo import fields, models


ACCOUNT_DOMAIN = "[('deprecated', '=', False), ('account_type', 'not in', ('asset_receivable', 'liability_payable', 'asset_cash', 'liability_credit_card', 'off_balance'))]"


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    property_account_external_income_id = fields.Many2one(
        'account.account', company_dependent=True,
        string='Conta de Rendimentos Externos', domain=ACCOUNT_DOMAIN,
    )
    property_account_external_expense_id = fields.Many2one(
        'account.account', company_dependent=True,
        string='Conta de Gastos Externos', domain=ACCOUNT_DOMAIN,
    )
