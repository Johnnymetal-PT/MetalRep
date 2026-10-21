# -*- coding: utf-8 -*-
"""Referência do cliente da venda de origem, exposta na Ordem de Fabrico.

O Nº de Encomenda já vem em ``mrp.production.origin`` (validado: no Piccolo
é o nome da venda). A "Referência do cliente" vive em
``sale.order.client_order_ref``, por isso é preciso chegar à venda de
origem. Usa-se a mesma expressão do standard ``sale_mrp`` (grupo de
aprovisionamento), igual à do módulo ``pg_purchase_sale_origin``.
"""
from odoo import models, fields


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    pg_client_order_ref = fields.Char(
        string="Referência do Cliente",
        compute='_compute_pg_client_order_ref',
        help="Referência do cliente (sale.order.client_order_ref) da venda "
             "de origem desta Ordem de Fabrico. Usado no cartão do Shop Floor.",
    )

    def _compute_pg_client_order_ref(self):
        for production in self:
            # Fabrico -> Venda: mesma travessia do standard sale_mrp.
            sale = (
                production.procurement_group_id
                .mrp_production_ids.move_dest_ids.group_id.sale_id[:1]
            )
            production.pg_client_order_ref = sale.client_order_ref or False
