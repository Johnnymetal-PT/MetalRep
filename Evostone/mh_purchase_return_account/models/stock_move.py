# -*- coding: utf-8 -*-
from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _get_src_account(self, accounts_data):
        """Nas devoluções a fornecedor (saída para local 'supplier'), usa a conta
        de devoluções da categoria como contrapartida da saída de stock, em vez
        da conta de entrada de stock. O local de origem continua a poder impor a
        sua própria conta (valuation_out_account_id), como no nativo.

        Só afeta devoluções de compra — `_is_returned('out')` é verdadeiro apenas
        para saídas cujo destino é um local de fornecedor."""
        if self._is_returned('out') and accounts_data.get('stock_return'):
            return (self.location_id.valuation_out_account_id.id
                    or accounts_data['stock_return'].id
                    or accounts_data['stock_input'].id)
        return super()._get_src_account(accounts_data)
