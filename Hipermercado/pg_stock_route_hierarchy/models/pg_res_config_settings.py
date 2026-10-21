"""Expoe a hierarquia de armazens em Definicoes (related fields).

Os 4 campos sao ``related="company_id.pg_*"`` para que a configuracao seja
sempre lida/escrita na ``res.company`` corrente -- o transient apenas serve
de ecra. As validacoes correm no proprio ``res.company`` (constraints +
``_pg_apply_stock_hierarchy``).
"""

from odoo import fields, models


class PgResConfigSettings(models.TransientModel):
    """Ecra Definicoes > Inventario > PG Stock Hierarchy."""

    _inherit = "res.config.settings"

    pg_sale_primary_warehouse_id = fields.Many2one(
        related="company_id.pg_sale_primary_warehouse_id",
        readonly=False,
    )
    pg_sale_secondary_warehouse_id = fields.Many2one(
        related="company_id.pg_sale_secondary_warehouse_id",
        readonly=False,
    )
    pg_sale_store_warehouse_id = fields.Many2one(
        related="company_id.pg_sale_store_warehouse_id",
        readonly=False,
    )
    pg_supplier_virtual_warehouse_id = fields.Many2one(
        related="company_id.pg_supplier_virtual_warehouse_id",
        readonly=False,
    )
