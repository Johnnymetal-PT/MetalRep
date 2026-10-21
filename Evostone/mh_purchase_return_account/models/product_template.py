# -*- coding: utf-8 -*-
from odoo import models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _get_product_accounts(self):
        """Injeta a conta de devoluções da categoria no dicionário de contas,
        para ser usada pela valorização de stock e pela nota de crédito."""
        accounts = super()._get_product_accounts()
        accounts['stock_return'] = self.categ_id.property_stock_account_return_categ_id
        return accounts
