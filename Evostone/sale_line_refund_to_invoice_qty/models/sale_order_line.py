# Copyright 2021 ForgeFlow (http://www.forgeflow.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    qty_refunded_not_invoiceable = fields.Float(
        compute="_compute_qty_refunded_not_invoiceable",
        string="Qtd. Devolvida Não Faturável",
        digits="Product Unit of Measure",
    )

    qty_returned_not_invoiceable = fields.Float(
        compute="_compute_qty_returned_not_invoiceable",
        string="Qtd. Devolvida Fisicamente Não Faturável",
        digits="Product Unit of Measure",
        help="Quantidade devolvida fisicamente (stock return) que não precisa ser faturada",
    )

    @api.depends(
        "invoice_lines.move_id.state",
        "invoice_lines.quantity",
        "untaxed_amount_to_invoice",
        "invoice_lines.sale_qty_to_reinvoice",
    )
    def _compute_qty_invoiced(self):
        res = super()._compute_qty_invoiced()
        # Revert effect of refunds in invoice_qty when `sale_qty_to_reinvoice`
        # is not set.
        for line in self:
            qty_invoiced = line.qty_invoiced
            for invoice_line in line.invoice_lines:
                if (
                    invoice_line.move_id.state != "cancel"
                    and invoice_line.move_id.move_type == "out_refund"
                    and not invoice_line.sale_qty_to_reinvoice
                ):
                    qty_invoiced += invoice_line.product_uom_id._compute_quantity(
                        invoice_line.quantity, line.product_uom
                    )
            if line.qty_invoiced != qty_invoiced:
                line.qty_invoiced = qty_invoiced
        return res

    @api.depends(
        "product_uom_qty",
        "invoice_lines.move_id.state",
        "invoice_lines.quantity",
        "invoice_lines.sale_qty_to_reinvoice",
    )
    def _compute_qty_refunded_not_invoiceable(self):
        for line in self:
            qty_ref_not_inv = 0.0
            for invoice_line in line.invoice_lines:
                if (
                    invoice_line.move_id.state != "cancel"
                    and invoice_line.move_id.move_type == "out_refund"
                    and not invoice_line.sale_qty_to_reinvoice
                ):
                    qty_ref_not_inv += invoice_line.product_uom_id._compute_quantity(
                        invoice_line.quantity, line.product_uom
                    )
            line.qty_refunded_not_invoiceable = qty_ref_not_inv

    @api.depends(
        "move_ids.state",
        "move_ids.quantity",
        "move_ids.picking_id.picking_type_id.code",
        "qty_invoiced",
        "qty_delivered",
    )
    def _compute_qty_returned_not_invoiceable(self):
        """
        Calcula a quantidade devolvida fisicamente que não precisa ser faturada.

        Cenário: Produto foi entregue e depois devolvido (return picking),
        mas nunca foi faturado. Neste caso, não faz sentido mostrar "a faturar".

        Lógica:
        - Soma as quantidades brutas de entregas (outgoing) e devoluções (incoming return)
        - Calcula devoluções líquidas = qty_returned - (qty_total_out - product_uom_qty)
          Ou seja, só conta devoluções que não foram compensadas por re-entregas
        - Se devoluções líquidas > qty_invoiced, a diferença é "não faturável"
        """
        for line in self:
            qty_returned = 0.0
            qty_out = 0.0
            for move in line.move_ids:
                if move.state != "done" or not move.picking_id:
                    continue
                picking_code = move.picking_id.picking_type_id.code
                if picking_code == "incoming" and move.origin_returned_move_id:
                    qty_returned += move.product_uom._compute_quantity(
                        move.quantity, line.product_uom
                    )
                elif picking_code == "outgoing":
                    qty_out += move.product_uom._compute_quantity(
                        move.quantity, line.product_uom
                    )

            # Só calcula devoluções líquidas se houve devoluções reais
            if qty_returned == 0:
                net_returned = 0.0
            else:
                # Devoluções líquidas: só as que não foram compensadas por re-entregas
                # Se entregou 3, devolveu 3, re-entregou 3: out=6, returned=3
                # net_returned = 3 - (6 - 3) = 0 (devolução foi compensada)
                net_returned = max(0.0, qty_returned - (qty_out - line.product_uom_qty))

            # Quantidade devolvida que não foi faturada = não precisa ser faturada
            # Se já foi faturado antes da devolução, precisa de nota de crédito (outro fluxo)
            qty_returned_not_inv = max(0.0, net_returned - line.qty_invoiced)
            line.qty_returned_not_invoiceable = qty_returned_not_inv

    @api.depends(
        "state",
        "product_uom_qty",
        "qty_delivered",
        "qty_to_invoice",
        "qty_invoiced",
        "qty_returned_not_invoiceable",
    )
    def _compute_invoice_status(self):
        """
        Override para considerar devoluções físicas no status de faturação.
        """
        res = super()._compute_invoice_status()
        for line in self:
            # Se toda a quantidade "a faturar" foi devolvida fisicamente sem fatura,
            # considerar como "faturado" (nada a fazer)
            if (
                line.invoice_status == "to invoice"
                and line.qty_returned_not_invoiceable > 0
                and line.qty_to_invoice <= line.qty_returned_not_invoiceable
            ):
                line.invoice_status = "invoiced"
        return res
