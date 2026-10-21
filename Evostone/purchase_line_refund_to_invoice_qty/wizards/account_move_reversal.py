from odoo import fields, models


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    purchase_qty_to_reinvoice = fields.Boolean(
        string="Re-faturar ao fornecedor",
        help="Marque se pretende re-faturar a mesma linha do pedido de compra",
        default=False,
    )

    def reverse_moves(self, is_modify=False):
        purchase_qty_to_reinvoice = (
            True if is_modify else self.purchase_qty_to_reinvoice
        )
        return super(
            AccountMoveReversal,
            self.with_context(
                purchase_qty_to_reinvoice=purchase_qty_to_reinvoice
            ),
        ).reverse_moves(is_modify=is_modify)
