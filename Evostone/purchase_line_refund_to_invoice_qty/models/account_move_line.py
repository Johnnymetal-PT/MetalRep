from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    purchase_qty_to_reinvoice = fields.Boolean(
        string="Re-faturar (Compra)",
        default=False,
        help="Marque se pretende re-faturar a mesma linha do pedido de compra",
        copy=False,
    )
