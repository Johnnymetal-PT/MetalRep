# -*- coding: utf-8 -*-
"""Hook no create da MO para ligar ao procurement group da venda.

Quando a MO e criada com `origin` igual ao nome de uma sale.order, o
hook copia o `procurement_group_id` da venda para a MO. Garante que o
smart button "Manufacturing Orders" no SO mostra esta MO.

Ver `__manifest__.py` para o guia completo.
"""

from odoo import models, api


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record, vals in zip(records, vals_list):
            record._update_procurement_group_from_sale()
        return records

    def _update_procurement_group_from_sale(self):
        """Se `origin` bater certo com o nome de um SO, copia o grupo.

        Custo: 1 search por MO. Cenarios em que `origin` nao e o nome
        de uma venda (ex.: MO criada manualmente) ficam intactas.
        """
        for production in self:
            if not production.origin:
                continue
            sale_order = self.env['sale.order'].search([
                ('name', '=', production.origin)
            ], limit=1)
            if sale_order:
                production.procurement_group_id = sale_order.procurement_group_id.id

