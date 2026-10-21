# -*- coding: utf-8 -*-
"""Ligação da Compra a Fornecedor à Venda a Cliente de origem.

Circuito Piccolo: Venda -> Fabrico -> Compra. O standard não expõe a
Venda na Compra (com o Fabrico pelo meio, o "Documento de origem" mostra
a Ordem de Fabrico ou fica vazio). Aqui reconstrói-se a ligação seguindo
a cadeia física de ``stock.move``:

    Compra  --(move_ids / move_dest_ids)-->  Ordem de Fabrico
            --(sale_mrp: grupo de aprovisionamento)-->  Venda

A parte Fabrico -> Venda usa a mesma expressão que o ``sale_mrp`` já usa
no botão "Source SO" da Ordem de Fabrico, por isso é tão fiável quanto o
standard. A parte Compra -> Fabrico segue a cadeia de movimentos (não o
grupo de aprovisionamento), para ser robusta independentemente da opção
de propagação de grupo da regra "Comprar".
"""
from odoo import models, fields


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    pg_sale_order_ids = fields.Many2many(
        'sale.order',
        string="Venda(s) a Cliente",
        compute='_compute_pg_sale_order_ids',
        help="Venda(s) a cliente na origem desta compra, seguindo o circuito "
             "Venda -> Fabrico -> Compra pela cadeia de movimentos de stock.",
    )
    pg_sale_order_id = fields.Many2one(
        'sale.order',
        string="Venda a Cliente",
        compute='_compute_pg_sale_order_ids',
        help="Venda a cliente na origem desta compra (a primeira, quando há "
             "mais do que uma). Em readonly funciona como link para a Venda; "
             "havendo várias, usar o botão \"Venda(s)\".",
    )
    pg_sale_order_count = fields.Integer(
        string="Nº de vendas de origem",
        compute='_compute_pg_sale_order_ids',
    )

    def _compute_pg_sale_order_ids(self):
        for order in self:
            productions = order._pg_get_source_productions()
            # Fabrico -> Venda: mesma travessia do standard sale_mrp.
            sale_orders = (
                productions.procurement_group_id
                .mrp_production_ids.move_dest_ids.group_id.sale_id
            )
            order.pg_sale_order_ids = sale_orders
            order.pg_sale_order_id = sale_orders[:1]
            order.pg_sale_order_count = len(sale_orders)

    def _pg_get_source_productions(self):
        """Ordens de Fabrico que esta Compra abastece.

        Segue a cadeia de ``stock.move`` para jusante a partir das linhas
        da compra até encontrar consumos de matéria-prima de uma Ordem de
        Fabrico (``raw_material_production_id``). Percorre passos
        intermédios (ex.: transferência de componentes em fabrico
        multi-etapa) com um limite de segurança para não ciclar.
        """
        self.ensure_one()
        Move = self.env['stock.move']
        # Movimentos imediatamente a jusante das linhas de compra: os
        # movimentos de receção (move_ids) e os "downstream moves" que a
        # linha regista diretamente (move_dest_ids).
        moves = self.order_line.move_ids.move_dest_ids | self.order_line.move_dest_ids
        productions = self.env['mrp.production']
        seen = Move
        # Limite de segurança: cadeias reais têm 1-3 saltos; 10 é folga.
        for _step in range(10):
            moves = moves - seen
            if not moves:
                break
            seen |= moves
            productions |= moves.raw_material_production_id
            moves = moves.move_dest_ids
        return productions

    def action_view_pg_sale_orders(self):
        self.ensure_one()
        sale_ids = self.pg_sale_order_ids.ids
        action = {
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
        }
        if len(sale_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': sale_ids[0],
            })
        else:
            action.update({
                'name': "Vendas a Cliente de origem",
                'domain': [('id', 'in', sale_ids)],
                'view_mode': 'tree,form',
            })
        return action
