# -*- coding: utf-8 -*-
"""Sinaliza, por encomenda, se o utilizador atual pode editar o preço das linhas.

O campo calculado é usado pela vista (sale_order_views.xml) para pôr `price_unit` em
só leitura. Ver o __manifest__.py para o objetivo e o grupo de segurança envolvido.
"""
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # Flag de UI: não é guardado, é recalculado para o utilizador atual em cada leitura.
    pg_sale_line_prices_readonly = fields.Boolean(
        compute="_compute_pg_sale_line_prices_readonly",
    )

    def _compute_pg_sale_line_prices_readonly(self):
        # True se o utilizador pertencer ao grupo de "preços só leitura". O valor é o
        # mesmo para todas as encomendas (depende do utilizador, não da encomenda),
        # por isso calcula-se uma vez e aplica-se a todo o recordset.
        readonly = self.env.user.has_group(
            "pg_sale_line_price_lock.group_sale_line_price_readonly"
        )
        for order in self:
            order.pg_sale_line_prices_readonly = readonly
