# Copyright 2025 MH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

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

    @api.depends('order_line.price_unit', 'order_line.product_uom_qty',
                 'order_line.discount', 'order_line.discount2',
                 'order_line.discount3', 'order_line.discount4',
                 'order_line.discounting_type', 'amount_untaxed')
    def _compute_discount_amounts(self):
        for order in self:
            total_undiscounted = 0.0
            currency = order.currency_id
            for line in order.order_line.filtered(lambda x: not x.display_type):
                # Calculate undiscounted amount (price * quantity without any discount)
                # Round per line to match price_subtotal rounding
                total_undiscounted += currency.round(line.price_unit * line.product_uom_qty)

            order.amount_undiscounted = total_undiscounted
            # order.amount_discount = total_undiscounted - order.amount_untaxed
            if (total_undiscounted - order.amount_untaxed >= 0):
                order.amount_discount = total_undiscounted - order.amount_untaxed
            else:
                order.amount_discount = 0

    @api.depends_context('lang')
    @api.depends('order_line.price_subtotal', 'currency_id', 'company_id',
                 'payment_term_id', 'amount_undiscounted', 'amount_discount')
    def _compute_tax_totals(self):
        """Compute tax totals with custom discount fields.
        Based on Odoo 18 official implementation.
        """
        AccountTax = self.env['account.tax']
        for order in self:
            order_lines = order.order_line.filtered(lambda x: not x.display_type)
            base_lines = [line._prepare_base_line_for_taxes_computation() for line in order_lines]
            base_lines += order._add_base_lines_for_early_payment_discount()
            AccountTax._add_tax_details_in_base_lines(base_lines, order.company_id)
            AccountTax._round_base_lines_tax_details(base_lines, order.company_id)

            # Atribuir tax_totals base (official Odoo 18 pattern)
            order.tax_totals = AccountTax._get_tax_totals_summary(
                base_lines=base_lines,
                currency=order.currency_id or order.company_id.currency_id,
                company=order.company_id,
            )

            # Adicionar campos customizados (in-place modification like account.move does)
            order.tax_totals['amount_undiscounted'] = order.amount_undiscounted
            order.tax_totals['formatted_amount_undiscounted'] = order.currency_id.format(order.amount_undiscounted)
            order.tax_totals['amount_discount'] = order.amount_discount
            order.tax_totals['formatted_amount_discount'] = order.currency_id.format(order.amount_discount)
