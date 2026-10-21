# -*- coding: utf-8 -*-
"""Navegacao em ambos os sentidos pela cadeia da subcontratacao (tarefa #8213).

Cadeia (Odoo 18, ensaio DEWA, NE A/00149):

    venda -> compra ao subcontratado -> rececao -> MO de subcontratacao
          -> componentes: reposicao (HMD/Stock -> subcontratado) e/ou
             compra de componentes -> rececao -> reposicao

O standard parte a cadeia em dois sitios: a MO de subcontratacao nasce num
grupo de aprovisionamento NOVO (com o nome da rececao) e sem linha de venda,
e as compras de componentes so se chegam a partir da MO. Por isso a venda
nao via as MO e nunca via as compras de componentes.

Aqui nao se cria nenhum campo armazenado nem se altera a ligacao: segue-se
a que o standard ja tem (move_orig_ids / move_dest_ids / purchase_line_id).

    venda       -> Subcontratacoes, Compras de componentes, Transferencias
    compra      -> Vendas, Subcontratacoes, Consumida em (fabrico)
    fabrico     -> Vendas, Compra ao subcontratado
"""

from odoo import api, fields, models, _


def _pg_open(records, name):
    """Abre o registo (1) ou a lista (varios), sem criar."""
    action = {
        'type': 'ir.actions.act_window',
        'name': name,
        'res_model': records._name,
        'context': {'create': False},
    }
    if len(records) == 1:
        action.update(view_mode='form', res_id=records.id)
    else:
        action.update(view_mode='list,form', domain=[('id', 'in', records.ids)])
    return action


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    pg_subcontract_count = fields.Integer(
        string="Subcontratacoes", compute='_compute_pg_subcontract_links',
        groups='mrp.group_mrp_user')
    pg_component_purchase_count = fields.Integer(
        string="Compras de componentes", compute='_compute_pg_subcontract_links',
        groups='purchase.group_purchase_user')
    pg_resupply_count = fields.Integer(
        string="Transferências de componentes", compute='_compute_pg_subcontract_links',
        groups='stock.group_stock_user')

    def _pg_subcontract_productions(self):
        """MO de subcontratacao geradas pelas compras desta venda."""
        self.ensure_one()
        if not self.procurement_group_id:
            return self.env['mrp.production']
        purchases = self.env['purchase.order'].search(self._related_purchase_domain())
        moves = purchases.order_line.move_ids.filtered('is_subcontract')
        return moves.move_orig_ids.production_id

    def _pg_component_purchases(self, productions):
        purchases = self.env['purchase.order']
        for production in productions:
            purchases |= production._get_purchase_orders()
        # A compra ao subcontratado nao e uma "compra de componentes".
        return purchases - self.env['purchase.order'].search(self._related_purchase_domain())

    @api.depends('procurement_group_id')
    def _compute_pg_subcontract_links(self):
        for order in self:
            productions = order._pg_subcontract_productions()
            order.pg_subcontract_count = len(productions)
            order.pg_component_purchase_count = len(order._pg_component_purchases(productions))
            order.pg_resupply_count = len(productions.picking_ids)

    def action_view_pg_subcontractions(self):
        self.ensure_one()
        return _pg_open(self._pg_subcontract_productions(), _("Subcontratações de %s", self.name))

    def action_view_pg_component_purchases(self):
        self.ensure_one()
        purchases = self._pg_component_purchases(self._pg_subcontract_productions())
        return _pg_open(purchases, _("Compras de componentes de %s", self.name))

    def action_view_pg_resupplies(self):
        self.ensure_one()
        return _pg_open(self._pg_subcontract_productions().picking_ids,
                        _("Transferências de componentes de %s", self.name))


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    pg_sale_order_count = fields.Integer(
        string="Vendas", compute='_compute_pg_links', groups='sales_team.group_sale_salesman')
    pg_subcontract_count = fields.Integer(
        string="Subcontratacoes", compute='_compute_pg_links', groups='mrp.group_mrp_user')
    pg_consumer_count = fields.Integer(
        string="Consumida em", compute='_compute_pg_links', groups='mrp.group_mrp_user')

    def _pg_subcontract_productions(self):
        moves = self.order_line.move_ids.filtered('is_subcontract')
        return moves.move_orig_ids.production_id

    def _pg_consumer_productions(self):
        """MO que consomem o que esta compra traz (compra de componentes)."""
        moves = self.order_line.move_ids | self.order_line.move_dest_ids
        dest_ids = moves._rollup_move_dests()
        return self.env['stock.move'].browse(list(dest_ids)).raw_material_production_id

    def _pg_sale_orders(self):
        """Vendas de origem: directas (grupo/linha) e via MO que a consome."""
        sales = self.env['sale.order']
        for purchase in self:
            moves = purchase.order_line.move_dest_ids
            sales |= (purchase.group_id | moves.group_id).sale_id
            sales |= purchase.order_line.sale_line_id.order_id
            sales |= purchase._pg_consumer_productions()._pg_sale_orders()
        return sales

    @api.depends('group_id', 'order_line')
    def _compute_pg_links(self):
        for purchase in self:
            purchase.pg_sale_order_count = len(purchase._pg_sale_orders())
            purchase.pg_subcontract_count = len(purchase._pg_subcontract_productions())
            purchase.pg_consumer_count = len(purchase._pg_consumer_productions())

    def action_view_pg_sale_orders(self):
        self.ensure_one()
        return _pg_open(self._pg_sale_orders(), _("Vendas de %s", self.name))

    def action_view_pg_subcontractions(self):
        self.ensure_one()
        return _pg_open(self._pg_subcontract_productions(), _("Subcontratações de %s", self.name))

    def action_view_pg_consumers(self):
        self.ensure_one()
        return _pg_open(self._pg_consumer_productions(), _("Fabrico que consome %s", self.name))


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    pg_sale_order_count = fields.Integer(
        string="Vendas", compute='_compute_pg_links', groups='sales_team.group_sale_salesman')
    pg_source_purchase_count = fields.Integer(
        string="Compra ao subcontratado", compute='_compute_pg_links',
        groups='purchase.group_purchase_user')

    def _pg_source_purchases(self):
        """Compra ao subcontratado de que esta MO de subcontratacao nasceu."""
        self.ensure_one()
        return self._get_subcontract_move().purchase_line_id.order_id

    def _pg_sale_orders(self):
        """Vendas de origem: MO de subcontratacao (via compra) e as que
        o standard ja liga pelo grupo."""
        sales = self.env['sale.order']
        for production in self:
            sales |= production.procurement_group_id.sale_id
            sales |= production._pg_source_purchases()._pg_sale_orders()
        return sales

    @api.depends('procurement_group_id', 'move_finished_ids.move_dest_ids')
    def _compute_pg_links(self):
        for production in self:
            production.pg_sale_order_count = len(production._pg_sale_orders())
            production.pg_source_purchase_count = len(production._pg_source_purchases())

    def action_view_pg_sale_orders(self):
        self.ensure_one()
        return _pg_open(self._pg_sale_orders(), _("Vendas de %s", self.name))

    def action_view_pg_source_purchase(self):
        self.ensure_one()
        return _pg_open(self._pg_source_purchases(), _("Compra ao subcontratado de %s", self.name))
