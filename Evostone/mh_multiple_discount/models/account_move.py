# Copyright 2025 MH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

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

    @api.depends('invoice_line_ids.price_unit', 'invoice_line_ids.quantity',
                 'invoice_line_ids.discount', 'invoice_line_ids.discount2',
                 'invoice_line_ids.discount3', 'invoice_line_ids.discount4',
                 'invoice_line_ids.discounting_type', 'amount_untaxed')
    def _compute_discount_amounts(self):
        for move in self:
            total_undiscounted = 0.0
            currency = move.currency_id
            for line in move.invoice_line_ids.filtered(lambda x: x.display_type == 'product'):
                # Calculate undiscounted amount (price * quantity without any discount)
                # Round per line to match price_subtotal rounding
                total_undiscounted += currency.round(line.price_unit * line.quantity)

            move.amount_undiscounted = total_undiscounted
            if (total_undiscounted - move.amount_untaxed >= 0):
                move.amount_discount = total_undiscounted - move.amount_untaxed
            else:
                move.amount_discount = 0

    @api.depends_context('lang')
    @api.depends(
        'invoice_line_ids.currency_rate',
        'invoice_line_ids.tax_base_amount',
        'invoice_line_ids.tax_line_id',
        'invoice_line_ids.price_total',
        'invoice_line_ids.price_subtotal',
        'invoice_payment_term_id',
        'partner_id',
        'currency_id',
        'amount_undiscounted',
        'amount_discount',
    )
    def _compute_tax_totals(self):
        """Computed field used for custom widget's rendering.
        Only set on invoices. Based on Odoo 18 official implementation.
        """
        for move in self:
            if move.is_invoice(include_receipts=True):
                base_lines, _tax_lines = move._get_rounded_base_and_tax_lines()

                # Atribuir tax_totals base (official Odoo 18 pattern)
                move.tax_totals = self.env['account.tax']._get_tax_totals_summary(
                    base_lines=base_lines,
                    currency=move.currency_id,
                    company=move.company_id,
                    cash_rounding=move.invoice_cash_rounding_id,
                )

                # Adicionar display_in_company_currency (from official Odoo 18)
                move.tax_totals['display_in_company_currency'] = (
                    move.company_id.display_invoice_tax_company_currency
                    and move.company_currency_id != move.currency_id
                    and move.tax_totals['has_tax_groups']
                    and move.is_sale_document(include_receipts=True)
                )

                # Adicionar campos customizados (in-place modification)
                move.tax_totals['amount_undiscounted'] = move.amount_undiscounted
                move.tax_totals['formatted_amount_undiscounted'] = move.currency_id.format(move.amount_undiscounted)
                move.tax_totals['amount_discount'] = move.amount_discount
                move.tax_totals['formatted_amount_discount'] = move.currency_id.format(move.amount_discount)
            else:
                # Non-invoice moves don't support that field
                move.tax_totals = None

    def _prepare_product_base_line_for_taxes_computation(self, product_line):
        """Override to inject aggregated discount from invoice line"""
        res = super()._prepare_product_base_line_for_taxes_computation(product_line)

        # If line has multiple discounts, use aggregated discount
        if hasattr(product_line, '_get_final_discount'):
            res['discount'] = product_line._get_final_discount()

        return res
