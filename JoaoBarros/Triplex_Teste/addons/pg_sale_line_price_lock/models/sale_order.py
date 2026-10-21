# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    pg_sale_line_prices_readonly = fields.Boolean(
        compute="_compute_pg_sale_line_prices_readonly",
    )

    def _compute_pg_sale_line_prices_readonly(self):
        readonly = self.env.user.has_group(
            "pg_sale_line_price_lock.group_sale_line_price_readonly"
        )
        for order in self:
            order.pg_sale_line_prices_readonly = readonly
