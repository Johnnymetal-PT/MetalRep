# -*- coding: utf-8 -*-
from odoo import models


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def _pg_purchase_order_from_lines(self, lines):
        """Encomenda de compra das faturas pagas, se for uma só; senão, vazio.

        `lines` são as linhas a pagar/receber do lote; a encomenda vem das linhas de
        produto das faturas (`purchase_line_id`). Faturas lançadas à mão, sem ligação às
        linhas da compra, não dão encomenda — liga-se depois no pagamento.
        """
        orders = lines.move_id.invoice_line_ids.purchase_line_id.order_id
        return orders if len(orders) == 1 else orders.browse()

    def _create_payment_vals_from_wizard(self, batch_result):
        vals = super()._create_payment_vals_from_wizard(batch_result)
        order = self._pg_purchase_order_from_lines(batch_result['lines'])
        if order:
            vals['pg_purchase_order_id'] = order.id
        return vals

    def _create_payment_vals_from_batch(self, batch_result):
        vals = super()._create_payment_vals_from_batch(batch_result)
        order = self._pg_purchase_order_from_lines(batch_result['lines'])
        if order:
            vals['pg_purchase_order_id'] = order.id
        return vals
