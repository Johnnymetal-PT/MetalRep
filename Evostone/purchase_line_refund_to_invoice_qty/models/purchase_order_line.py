from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    qty_refunded_not_invoiceable = fields.Float(
        compute="_compute_qty_refunded_not_invoiceable",
        string="Qtd. NC Não Faturável",
        digits="Product Unit of Measure",
    )

    qty_returned_not_invoiceable = fields.Float(
        compute="_compute_qty_returned_not_invoiceable",
        string="Qtd. Devolvida Não Faturável",
        digits="Product Unit of Measure",
        help="Quantidade devolvida ao fornecedor que não precisa ser faturada",
    )

    @api.depends(
        "move_ids.state",
        "move_ids.quantity",
        "move_ids.picking_id.picking_type_id.code",
        "qty_invoiced",
    )
    def _compute_qty_returned_not_invoiceable(self):
        """Calcula a quantidade devolvida ao fornecedor que não precisa ser faturada.

        Cenário: Produto foi recebido e depois devolvido (return picking),
        mas nunca foi faturado. Neste caso, não faz sentido mostrar "a faturar".
        """
        for line in self:
            qty_returned = 0.0
            for move in line.move_ids:
                if (
                    move.state == "done"
                    and move.picking_id
                    and move.picking_id.picking_type_id.code == "outgoing"
                    and move.origin_returned_move_id
                ):
                    qty_returned += move.product_uom._compute_quantity(
                        move.quantity, line.product_uom
                    )
            line.qty_returned_not_invoiceable = max(0.0, qty_returned - line.qty_invoiced)

    @api.depends(
        "invoice_lines.move_id.state",
        "invoice_lines.quantity",
        "invoice_lines.purchase_qty_to_reinvoice",
        "qty_returned_not_invoiceable",
    )
    def _compute_qty_invoiced(self):
        """Override para:
        1. Reverter efeito das notas de crédito no qty_invoiced quando
           purchase_qty_to_reinvoice não está marcado.
        2. Recalcular qty_to_invoice com o qty_invoiced corrigido.
        3. Forçar qty_to_invoice = 0 quando devoluções físicas cobrem o valor.
        """
        res = super()._compute_qty_invoiced()
        for line in self:
            # 1. Notas de crédito: não reduzir qty_invoiced se não é para re-faturar
            qty_invoiced = line.qty_invoiced
            for invoice_line in line.invoice_lines:
                if (
                    invoice_line.move_id.state != "cancel"
                    and invoice_line.move_id.move_type == "in_refund"
                    and not invoice_line.purchase_qty_to_reinvoice
                ):
                    qty_invoiced += invoice_line.product_uom_id._compute_quantity(
                        invoice_line.quantity, line.product_uom
                    )
            if line.qty_invoiced != qty_invoiced:
                line.qty_invoiced = qty_invoiced
                # 2. Recalcular qty_to_invoice com o novo qty_invoiced
                if line.order_id.state in ['purchase', 'done']:
                    if line.product_id.purchase_method == 'purchase':
                        line.qty_to_invoice = line.product_qty - line.qty_invoiced
                    else:
                        line.qty_to_invoice = line.qty_received - line.qty_invoiced
                else:
                    line.qty_to_invoice = 0

            # 3. Devoluções físicas: forçar qty_to_invoice = 0
            if (
                line.qty_to_invoice > 0
                and line.qty_returned_not_invoiceable > 0
                and line.qty_to_invoice <= line.qty_returned_not_invoiceable
            ):
                line.qty_to_invoice = 0
        return res

    @api.depends(
        "product_qty",
        "invoice_lines.move_id.state",
        "invoice_lines.quantity",
        "invoice_lines.purchase_qty_to_reinvoice",
    )
    def _compute_qty_refunded_not_invoiceable(self):
        for line in self:
            qty_ref_not_inv = 0.0
            for invoice_line in line.invoice_lines:
                if (
                    invoice_line.move_id.state != "cancel"
                    and invoice_line.move_id.move_type == "in_refund"
                    and not invoice_line.purchase_qty_to_reinvoice
                ):
                    qty_ref_not_inv += invoice_line.product_uom_id._compute_quantity(
                        invoice_line.quantity, line.product_uom
                    )
            line.qty_refunded_not_invoiceable = qty_ref_not_inv
