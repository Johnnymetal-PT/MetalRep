from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _create_invoices(self, grouped=False, final=False, date=None):
        """Após criar as faturas, propaga a morada de entrega da guia para
        cada fatura (ver `account.move._pg_apply_picking_delivery_address`)."""
        moves = super()._create_invoices(grouped=grouped, final=final, date=date)
        moves._pg_apply_picking_delivery_address()
        return moves
