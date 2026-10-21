# -*- coding: utf-8 -*-
"""Smart buttons para Purchase Orders e Manufacturing Orders.

A ligacao entre venda e PO/MO e feita pelo `procurement.group`
(criado quando a venda dispara MTO). O override de `action_confirm`
mantem o `origin` em PO/MO alinhado quando a venda muda de nome.

Ver `__manifest__.py` para o guia completo.
"""

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    purchase_order_count = fields.Integer(
        string="Purchase Order Count",
        compute="_compute_purchase_order_count",
    )

    mrp_production_count = fields.Integer(
        compute="_compute_mrp_production_count",
    )

    def _related_purchase_domain(self):
        """Dominio das compras ligadas a esta venda.

        Alem do grupo de aprovisionamento da venda, segue as linhas de
        compra cujos movimentos de destino pertencem a esse grupo: quando
        duas RFQ sao fundidas (Fundir), as linhas passam para a RFQ mais
        antiga, que tem o grupo de OUTRA venda, e a venda da RFQ cancelada
        deixava de ver a compra onde as suas linhas estao agora.
        """
        self.ensure_one()
        group = self.procurement_group_id
        return ['|', ('group_id', '=', group.id),
                ('order_line.move_dest_ids.group_id', '=', group.id)]

    @api.depends('procurement_group_id')
    def _compute_purchase_order_count(self):
        """Count purchase orders linked by procurement group or merged lines."""
        for order in self:
            group = order.procurement_group_id
            if group:
                domain = order._related_purchase_domain()
                count = self.env['purchase.order'].search_count(domain)
                _logger.debug(
                    "Found %s purchase orders for SO %s via group %s",
                    count,
                    order.name,
                    group.id,
                )
                order.purchase_order_count = count
            else:
                order.purchase_order_count = 0

    def action_view_related_purchase_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Orders',
            'res_model': 'purchase.order',
            'view_mode': 'list,form',
            'domain': self._related_purchase_domain(),
            'context': {'create': False},
        }

    @api.depends('procurement_group_id')
    def _compute_mrp_production_count(self):
        """Count manufacturing orders linked by procurement group."""
        for order in self:
            group = order.procurement_group_id
            if group:
                domain = [('procurement_group_id', '=', group.id)]
                mo_count = self.env['mrp.production'].search_count(domain)
                _logger.debug(
                    "Found %s manufacturing orders for SO %s via group %s",
                    mo_count,
                    order.name,
                    group.id,
                )
                order.mrp_production_count = mo_count
            else:
                order.mrp_production_count = 0

    def action_view_related_mos(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Manufacturing Orders',
            'res_model': 'mrp.production',
            'view_mode': 'list,form',
            'domain': [('procurement_group_id', '=', self.procurement_group_id.id)],
            'context': {'create': False},
        }

    def action_confirm(self):
        # Captura o nome ANTES do super: o standard pode renomear a
        # venda no confirm (draft -> sequencia final). Depois propaga
        # esse rename ao `origin` de POs/MOs criadas com o nome antigo
        # (caso comum em fluxos MTO em que a PO existia em RFQ no SO
        # ainda draft).
        old_names = {order.id: order.name for order in self}
        res = super().action_confirm()
        for order in self:
            old_name = old_names.get(order.id)
            new_name = order.name
            if old_name and new_name and old_name != new_name:
                purchases = self.env['purchase.order'].search([
                    ('origin', '=', old_name)
                ])
                if purchases:
                    purchases.write({'origin': new_name})
                mos = self.env['mrp.production'].search([
                    ('origin', '=', old_name)
                ])
                if mos:
                    # Sincroniza tambem o procurement_group_id da MO -
                    # complementa o hook em mrp.production.create
                    # quando a MO existia antes do confirm da venda.
                    mos.write({
                        'origin': new_name,
                        'procurement_group_id': order.procurement_group_id.id,
                    })
        return res

