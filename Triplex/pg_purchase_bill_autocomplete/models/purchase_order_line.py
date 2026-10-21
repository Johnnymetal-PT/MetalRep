# -*- coding: utf-8 -*-
"""Linhas a 0 € ainda por faturar vêm para a fatura com a quantidade encomendada."""
from odoo import models
from odoo.tools import float_is_zero


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def _pg_is_unbilled_zero_price(self):
        """Linha a 0 €, com quantidade e sem qualquer faturação."""
        self.ensure_one()
        rounding = self.currency_id.rounding or 0.01
        return (
            not self.display_type
            and float_is_zero(self.price_unit, precision_rounding=rounding)
            and self.product_qty > 0
            and float_is_zero(self.qty_invoiced, precision_rounding=self.product_uom.rounding)
        )

    def _prepare_account_move_line(self, move=False):
        res = super()._prepare_account_move_line(move)
        # Com faturação por quantidade recebida, `qty_to_invoice` é 0 numa linha ainda não
        # recebida; usa-se a quantidade encomendada para o utilizador só indicar o preço.
        if self._pg_is_unbilled_zero_price() and not res.get('quantity'):
            res['quantity'] = self.product_qty
        return res
