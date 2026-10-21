"""Stat buttons na Sale Order para MOs e Compras de componentes.

Reconstroi a ligacao SO -> MO -> PO atraves do
``procurement.group``, com fallback por ``origin`` (string match no nome
do documento) porque na Piccolo cada MO tem o seu proprio procurement
group nomeado a partir da propria MO.
"""
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    pg_purchase_order_count = fields.Integer(
        string='Compras Componentes',
        compute='_compute_pg_purchase_order_count',
    )

    pg_mrp_production_count = fields.Integer(
        string='Ordens de Produção',
        compute='_compute_pg_mrp_production_count',
    )

    def _pg_get_related_mos(self):
        """Devolve as MOs associadas a esta SO.

        Em Piccolo cada MO recebe um ``procurement_group_id`` proprio
        (com o nome da MO), pelo que o match por ``group_id`` sozinho
        nao chega. Une-se com o match por ``origin == SO.name`` para
        recuperar a ligacao em ambos os fluxos.
        """
        self.ensure_one()
        Mo = self.env['mrp.production']
        mos = Mo
        if self.procurement_group_id:
            mos |= Mo.search([
                ('procurement_group_id', '=', self.procurement_group_id.id),
                ('state', '!=', 'cancel'),
            ])
        if self.name:
            mos |= Mo.search([
                ('origin', '=', self.name),
                ('state', '!=', 'cancel'),
            ])
        return mos

    def _pg_get_related_purchase_orders(self):
        """SO -> MO (via origin) -> PO (via PO.group_id == MO.procurement_group_id).

        Em Piccolo cada MO possui um procurement_group_id com o nome da
        propria MO; as POs geradas para os seus componentes partilham
        esse mesmo group_id. Procuramos POs por ``group_id`` e tambem
        unimos por ``origin == MO.name`` como rede de seguranca para POs
        onde a ligacao por group_id se perdeu em customizacoes.
        """
        self.ensure_one()
        mos = self._pg_get_related_mos()
        if not mos:
            return self.env['purchase.order']
        Po = self.env['purchase.order']
        pos = Po
        mo_groups = mos.procurement_group_id
        if mo_groups:
            pos |= Po.search([('group_id', 'in', mo_groups.ids)])
        mo_names = [n for n in mos.mapped('name') if n]
        if mo_names:
            pos |= Po.search([('origin', 'in', mo_names)])
        return pos

    @api.depends('procurement_group_id', 'name')
    def _compute_pg_mrp_production_count(self):
        for order in self:
            order.pg_mrp_production_count = len(order._pg_get_related_mos())

    @api.depends('procurement_group_id', 'name')
    def _compute_pg_purchase_order_count(self):
        for order in self:
            order.pg_purchase_order_count = len(order._pg_get_related_purchase_orders())

    def action_view_pg_related_purchase_orders(self):
        self.ensure_one()
        purchase_orders = self._pg_get_related_purchase_orders()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Compras de Componentes',
            'res_model': 'purchase.order',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', purchase_orders.ids)],
            # create:False evita confusao do utilizador ao querer criar
            # uma PO de raiz a partir do botao da SO.
            'context': {'create': False},
        }

    def action_view_pg_related_mos(self):
        self.ensure_one()
        mos = self._pg_get_related_mos()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ordens de Produção',
            'res_model': 'mrp.production',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', mos.ids)],
            'context': {'create': False},
        }
