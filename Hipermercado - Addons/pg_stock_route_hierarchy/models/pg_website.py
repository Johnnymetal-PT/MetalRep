"""Disponibilidade do produto na loja online -- alinhada com a hierarquia."""

from odoo import models


class PgWebsite(models.Model):
    """Override que faz o website usar a hierarquia + virtual supplier."""

    _inherit = "website"

    def _get_product_available_qty(self, product, **kwargs):
        # Esta funcao alimenta o badge de disponibilidade na pagina publica
        # do produto. Sem este override, o cliente final veria apenas o
        # stock fisico do armazem do website; agora ve o numero que a SO
        # ira de facto considerar (mesmo total usado em ``_get_free_qty``).
        self.ensure_one()
        if self.company_id.pg_sale_primary_warehouse_id:
            return self.company_id._pg_get_sale_available_qty(product, warehouse=self.warehouse_id)
        return super()._get_product_available_qty(product, **kwargs)
