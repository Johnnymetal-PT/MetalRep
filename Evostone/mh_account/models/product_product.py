# -*- coding: utf-8 -*-
from odoo import fields, models


ACCOUNT_DOMAIN = "[('deprecated', '=', False), ('account_type', 'not in', ('asset_receivable', 'liability_payable', 'asset_cash', 'liability_credit_card', 'off_balance'))]"


class ProductProduct(models.Model):
    _inherit = 'product.product'

    variant_property_account_income_id = fields.Many2one(
        'account.account', company_dependent=True, ondelete='restrict',
        string='Conta de Receita (Variante)', domain=ACCOUNT_DOMAIN,
    )
    variant_property_account_expense_id = fields.Many2one(
        'account.account', company_dependent=True, ondelete='restrict',
        string='Conta de Gasto (Variante)', domain=ACCOUNT_DOMAIN,
    )
    variant_property_account_external_income_id = fields.Many2one(
        'account.account', company_dependent=True, ondelete='restrict',
        string='Conta de Receita Externa (Variante)', domain=ACCOUNT_DOMAIN,
    )
    variant_property_account_external_expense_id = fields.Many2one(
        'account.account', company_dependent=True, ondelete='restrict',
        string='Conta de Gasto Externa (Variante)', domain=ACCOUNT_DOMAIN,
    )
