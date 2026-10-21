# Copyright 2025 MH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    amount_undiscounted = fields.Monetary(
        string="SUBTOTAL",
        compute='_compute_discount_amounts',
        store=True,
        help="Subtotal sem descontos e sem impostos"
    )

    amount_discount = fields.Monetary(
        string="Desc.",
        compute='_compute_discount_amounts',
        store=True,
        help="Total de desconto aplicado"
    )

    @api.depends('order_line.price_unit', 'order_line.product_qty',
                 'order_line.discount', 'amount_untaxed')
    def _compute_discount_amounts(self):
        for move in self:
            total_undiscounted = 0.0
            currency = move.currency_id
            for line in move.order_line:
                # Calculate undiscounted amount (price * product_qty without any discount)
                # Round per line to match price_subtotal rounding
                total_undiscounted += currency.round(line.price_unit * line.product_qty)

            move.amount_undiscounted = total_undiscounted
            if (total_undiscounted - move.amount_untaxed >= 0):
                move.amount_discount = total_undiscounted - move.amount_untaxed
            else:
                move.amount_discount = 0