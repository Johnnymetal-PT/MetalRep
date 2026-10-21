# -*- coding: utf-8 -*-
"""Totais e linhas de packing em `sale.order` / `sale.order.line`.

Propagacao bidirecional: a linha de venda calcula os seus campos
`line_packing_*` a partir do produto/qty, e em paralelo sincroniza
os `stock.move` ligados (`_sync_move_packing`). Isto e o que mantem o
operador logistico a ver os mesmos numeros que o comercial.

Ver `__manifest__.py` para o guia completo.
"""

from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    total_packing_volumes = fields.Float(
        string='Total Volumes',
        digits=(4, 2),
        compute='_compute_packing_totals',
        store=True,
        help='Total de volumes de todos os produtos na venda'
    )

    total_packing_weight = fields.Float(
        string='Total Peso (Kg)',
        digits=(4, 2),
        compute='_compute_packing_totals',
        store=True,
        help='Peso total de todos os produtos na venda'
    )

    total_packing_cubicagem = fields.Float(
        string='Total Cubicagem',
        digits=(4, 2),
        compute='_compute_packing_totals',
        store=True,
        help='Cubicagem total de todos os produtos na venda'
    )

    @api.depends('order_line.product_id.packing_volumes',
                 'order_line.product_id.packing_weight',
                 'order_line.product_id.packing_cubicagem',
                 'order_line.product_uom_qty')
    def _compute_packing_totals(self):
        for order in self:
            total_volumes = 0.0
            total_weight = 0.0
            total_cubicagem = 0.0
            for line in order.order_line:
                if line.product_id:
                    qty = line.product_uom_qty
                    total_volumes += line.product_id.packing_volumes * qty
                    total_weight += line.product_id.packing_weight * qty
                    total_cubicagem += line.product_id.packing_cubicagem * qty
            order.total_packing_volumes = total_volumes
            order.total_packing_weight = total_weight
            order.total_packing_cubicagem = total_cubicagem


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    line_packing_volumes = fields.Float(
        string='Volumes',
        digits=(4, 2),
        compute='_compute_line_packing',
        store=True,
        help='Volumes para esta linha baseado no produto e quantidade'
    )

    line_packing_weight = fields.Float(
        string='Peso (Kg)',
        digits=(4, 2),
        compute='_compute_line_packing',
        store=True,
        help='Peso para esta linha baseado no produto e quantidade'
    )

    line_packing_cubicagem = fields.Float(
        string='Cubicagem',
        digits=(4, 2),
        compute='_compute_line_packing',
        store=True,
        help='Cubicagem para esta linha baseado no produto e quantidade'
    )

    def _sync_move_packing(self):
        """Replica `line_packing_*` da venda para os `stock.move` ligados.

        Efeito colateral usado tanto no compute como no write: garante que
        o operador logistico ve sempre os mesmos numeros que o comercial.
        Custo: 1 search + 1 write por chunk; aceitavel no contexto HMD.
        """
        moves = self.env['stock.move'].search([('sale_line_id', 'in', self.ids)])
        for line in self:
            related_moves = moves.filtered(lambda m: m.sale_line_id == line)
            if related_moves:
                related_moves.write({
                    'move_packing_volumes': line.line_packing_volumes,
                    'move_packing_weight': line.line_packing_weight,
                    'move_packing_cubicagem': line.line_packing_cubicagem,
                })

    def write(self, vals):
        res = super().write(vals)
        # Override do write: quando o wizard ou o utilizador editam os
        # campos line_packing_* da linha de venda, propagar para os
        # stock.move ligados (o compute nao corre se forem definidos
        # diretamente sem alterar produto/qty).
        packing_fields = {'line_packing_volumes', 'line_packing_weight', 'line_packing_cubicagem'}
        if packing_fields.intersection(vals.keys()):
            self._sync_move_packing()
        return res

    @api.depends('product_id.packing_volumes',
                 'product_id.packing_weight',
                 'product_id.packing_cubicagem',
                 'product_uom_qty')
    def _compute_line_packing(self):
        for line in self:
            if line.product_id:
                qty = line.product_uom_qty
                line.line_packing_volumes = line.product_id.packing_volumes * qty
                line.line_packing_weight = line.product_id.packing_weight * qty
                line.line_packing_cubicagem = line.product_id.packing_cubicagem * qty
            else:
                line.line_packing_volumes = 0.0
                line.line_packing_weight = 0.0
                line.line_packing_cubicagem = 0.0
            line._sync_move_packing()

    def action_open_line_calc_wizard(self):
        self.ensure_one()
        return {
            'name': 'Cálculo de Cubicagem da Linha',
            'type': 'ir.actions.act_window',
            'res_model': 'cubicagem.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_line_id': self.id,
            }
        }
