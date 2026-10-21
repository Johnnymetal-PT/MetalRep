from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    # ------------------------------------------------------------------
    # Morada de entrega da guia -> morada de entrega da fatura
    # ------------------------------------------------------------------
    def _pg_apply_picking_delivery_address(self):
        """Define o `partner_shipping_id` da fatura com a morada de entrega
        materializada na guia de origem.

        Percurso: fatura -> linhas -> linhas de venda -> ordens de venda ->
        guias de saída. De entre as guias com morada de entrega criada por
        `pg_stock_delivery_address`, é usada a **primeira entrega**
        (cronológica). A morada é tornada permanente para nunca ser removida
        pela limpeza mensal, já que passa a constar num documento fiscal.
        """
        for move in self:
            if move.move_type not in ("out_invoice", "out_refund"):
                continue

            orders = move.line_ids.sale_line_ids.order_id
            if not orders:
                continue

            pickings = orders.picking_ids.filtered(
                lambda p: p.picking_type_code == "outgoing"
                and p.pg_delivery_address_id
            )
            if not pickings:
                continue

            picking = move._pg_first_delivery_picking(pickings)
            address = picking.pg_delivery_address_id

            if move.partner_shipping_id != address:
                move.partner_shipping_id = address.id

            # A morada passa a viver num documento fiscal: excluí-la da
            # limpeza periódica para não deixar a fatura ligada a um contacto
            # que o cron tentaria remover.
            if address.pg_picking_delivery_address:
                address.pg_picking_delivery_address = False

    @staticmethod
    def _pg_first_delivery_picking(pickings):
        """Primeira guia de entrega (cronológica) de entre as candidatas."""
        def sort_key(picking):
            return (
                picking.date_done
                or picking.scheduled_date
                or picking.create_date,
                picking.id,
            )
        return pickings.sorted(key=sort_key)[0]
