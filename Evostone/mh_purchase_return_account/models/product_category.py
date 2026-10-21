# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = 'product.category'

    # Contrapartida das devoluções a fornecedor (ex.: 217 Devoluções de compras).
    # Segue o padrão das contas de stock nativas (company_dependent).
    property_stock_account_return_categ_id = fields.Many2one(
        'account.account', string='Conta de Devolução de Compras',
        company_dependent=True, ondelete='restrict',
        domain="[('deprecated', '=', False)]", check_company=True,
        help="Conta usada nas devoluções a fornecedor — tanto no picking de "
             "devolução (contrapartida da saída de stock) como na nota de "
             "crédito de compra. Se vazia, mantém-se o comportamento nativo "
             "(conta de entrada de stock).")
