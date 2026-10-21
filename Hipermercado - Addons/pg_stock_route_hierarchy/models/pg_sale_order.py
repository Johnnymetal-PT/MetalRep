"""Encomendas de venda alinhadas com a hierarquia de armazens do PG."""

from odoo import models


class PgSaleOrder(models.Model):
    """Forca o armazem primario nas SOs do website e usa a soma da hierarquia."""

    _inherit = "sale.order"

    def _compute_warehouse_id(self):
        # Mantem o comportamento standard para SOs internas (B2B/backoffice) e
        # apenas sobrepoe nas SOs originadas no website. Garante que o
        # checkout publico nunca acaba a reservar de um armazem secundario
        # ou de outra empresa.
        super()._compute_warehouse_id()
        for order in self.filtered("website_id"):
            primary_wh = order.company_id.pg_sale_primary_warehouse_id
            if primary_wh:
                order.warehouse_id = primary_wh

    def _get_free_qty(self, product):
        # Se a hierarquia esta configurada, devolve a soma "interno (hierarquia)
        # + virtual supplier"; caso contrario, comportamento Odoo standard.
        self.ensure_one()
        if self.company_id.pg_sale_primary_warehouse_id:
            return self.company_id._pg_get_sale_available_qty(product, warehouse=self.warehouse_id)
        return super()._get_free_qty(product)
