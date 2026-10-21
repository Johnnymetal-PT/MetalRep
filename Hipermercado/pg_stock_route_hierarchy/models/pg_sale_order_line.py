"""Linhas de venda: leitura de quantidades + injecao de routes custom."""

from odoo import models


class PgSaleOrderLine(models.Model):
    """Override de ``_read_qties`` e ``_prepare_procurement_values``."""

    _inherit = "sale.order.line"

    def _read_qties(self, date, wh):
        # Esta sobrescreve as quantidades que o Odoo mostra no popup da linha
        # da venda. Sem isto, o utilizador veria apenas o stock do armazem
        # da SO; agora ve o total que de facto e vendavel (soma hierarquia
        # interna + virtual supplier). ``virtual_available`` e alinhado com
        # ``free_qty`` para nao confundir o utilizador.
        quantities = super()._read_qties(date, wh)
        if not self:
            return quantities
        lines_by_product = {line.product_id.id: line for line in self if line.product_id}
        for values in quantities:
            line = lines_by_product.get(values.get("id"))
            if not line or not line.company_id.pg_sale_primary_warehouse_id:
                continue
            product = line.product_id
            values["qty_available"] = line.company_id._pg_get_internal_sale_available_qty(product, warehouse=line.warehouse_id)
            values["free_qty"] = line.company_id._pg_get_sale_available_qty(product, warehouse=line.warehouse_id)
            values["virtual_available"] = values["free_qty"]
        return quantities

    def _prepare_procurement_values(self):
        # Junta as routes custom calculadas em
        # ``res.company._pg_get_sale_supply_routes`` as routes ja definidas
        # pelo Odoo. Permite que o procurement engine considere a rota de
        # compra associada ao primario quando o stock interno nao chega.
        values = super()._prepare_procurement_values()
        routes = self.order_id.company_id._pg_get_sale_supply_routes(self.order_id.warehouse_id)
        if routes:
            values["route_ids"] |= routes
        return values
