# -*- coding: utf-8 -*-
"""Vista `purchase_bill_union` que mantém compras com linhas a 0 € por faturar."""
from odoo import models, tools


class PurchaseBillUnion(models.Model):
    _inherit = 'purchase.bill.union'

    def init(self):
        # Mesma vista do core (purchase/report/purchase_bill.py), com um OR extra nas compras.
        tools.drop_view_if_exists(self.env.cr, 'purchase_bill_union')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW purchase_bill_union AS (
                SELECT
                    id, name, ref as reference, partner_id, date, amount_untaxed as amount, currency_id, company_id,
                    id as vendor_bill_id, NULL as purchase_order_id
                FROM account_move
                WHERE
                    move_type='in_invoice' and state = 'posted'
            UNION
                SELECT
                    -po.id, po.name, po.partner_ref as reference, po.partner_id, po.date_order::date as date,
                    po.amount_untaxed as amount, po.currency_id, po.company_id,
                    NULL as vendor_bill_id, po.id as purchase_order_id
                FROM purchase_order po
                WHERE
                    po.state in ('purchase', 'done') AND (
                        po.invoice_status in ('to invoice', 'no')
                        OR EXISTS (
                            SELECT 1 FROM purchase_order_line pol
                            WHERE pol.order_id = po.id
                              AND pol.display_type IS NULL
                              AND COALESCE(pol.price_unit, 0) = 0
                              AND pol.product_qty > 0
                              AND COALESCE(pol.qty_invoiced, 0) = 0
                        )
                    )
            )""")
