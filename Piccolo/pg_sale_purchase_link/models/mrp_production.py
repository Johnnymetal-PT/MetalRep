"""Backfill do procurement_group da MO a partir da Sale Order.

Quando uma MO e criada sem ``procurement_group_id`` mas tem ``origin``,
este override vai buscar o grupo da SO correspondente e copia para a MO.
Restaura a ligacao SO<->MO em fluxos onde o grupo se perde (ex.: MOs
criadas manualmente reaproveitando o nome da SO no campo origin).
"""
from odoo import api, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            record._pg_backfill_procurement_group_from_sale()
        return records

    def _pg_backfill_procurement_group_from_sale(self):
        for production in self:
            # Se ja tem grupo, ou se nao sabemos a SO (sem origin), nao faz nada.
            if production.procurement_group_id or not production.origin:
                continue
            sale_order = self.env['sale.order'].search(
                [('name', '=', production.origin)], limit=1,
            )
            if sale_order and sale_order.procurement_group_id:
                production.procurement_group_id = sale_order.procurement_group_id.id
