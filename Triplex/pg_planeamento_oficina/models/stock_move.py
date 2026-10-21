# -*- coding: utf-8 -*-
"""Classifica cada movimento de componente pelo tipo de fornecedor.

O tipo/fornecedor é derivado do primeiro vendedor do produto que tenha x_supplier_type
definido. Isto alimenta as colunas de componentes do painel. Ver o __manifest__.py.
"""
from odoo import api, fields, models

from .res_partner import SUPPLIER_TYPES


# Estado do componente no painel de planeamento (móvel de matéria-prima):
# - recebido    : já disponível em stock (movimento reservado ou concluído)
# - encomendado : PO confirmada mas a receção de artigos ainda não foi feita
# - falta       : sem stock e sem PO confirmada (ainda por encomendar)
PLANEAMENTO_MOVE_STATUS = [
    ('recebido', 'Recebido'),
    ('encomendado', 'Encomendado'),
    ('falta', 'Em Falta'),
]


class StockMove(models.Model):
    _inherit = 'stock.move'

    x_supplier_type = fields.Selection(
        SUPPLIER_TYPES,
        string='Tipo de Fornecedor',
        compute='_compute_x_supplier_type',
        store=True,
    )
    x_vendor_id = fields.Many2one(
        'res.partner',
        string='Fornecedor',
        compute='_compute_x_supplier_type',
        store=True,
    )
    x_planeamento_status = fields.Selection(
        PLANEAMENTO_MOVE_STATUS,
        string='Estado',
        compute='_compute_planeamento_status',
        store=True,
    )
    x_planeamento_line_id = fields.Many2one(
        'pg.planeamento.line',
        string='Planeamento',
        compute='_compute_planeamento_line',
        store=True,
        help='Linha de planeamento (encomenda) a que este componente pertence.',
    )

    @api.depends('product_id', 'product_id.seller_ids',
                 'product_id.seller_ids.partner_id.x_supplier_type',
                 'product_id.seller_ids.sequence')
    def _compute_x_supplier_type(self):
        for move in self:
            sellers = move.product_id.seller_ids.sorted('sequence')
            typed = sellers.filtered(lambda s: s.partner_id.x_supplier_type)
            if typed:
                move.x_supplier_type = typed[0].partner_id.x_supplier_type
                move.x_vendor_id = typed[0].partner_id
            else:
                move.x_supplier_type = False
                move.x_vendor_id = False

    @api.depends('state', 'move_orig_ids.state',
                 'move_orig_ids.purchase_line_id.order_id.state')
    def _compute_planeamento_status(self):
        for move in self:
            if move.state in ('done', 'assigned'):
                # Componente disponível em stock (reservado ou consumido).
                move.x_planeamento_status = 'recebido'
            elif any(line.order_id.state in ('purchase', 'done')
                     for line in move.move_orig_ids.purchase_line_id):
                # Existe PO confirmada a abastecer, mas ainda sem receção.
                move.x_planeamento_status = 'encomendado'
            else:
                move.x_planeamento_status = 'falta'

    @api.depends('raw_material_production_id',
                 'raw_material_production_id.origin',
                 'raw_material_production_id.product_id')
    def _compute_planeamento_line(self):
        Planeamento = self.env['pg.planeamento.line']
        for move in self:
            mo = move.raw_material_production_id
            line = Planeamento
            if mo and mo.origin and mo.product_id:
                line = Planeamento.search([
                    ('sale_line_id.order_id.name', '=', mo.origin),
                    ('sale_line_id.product_id', '=', mo.product_id.id),
                ], limit=1)
            move.x_planeamento_line_id = line

    def action_open_planeamento(self):
        self.ensure_one()
        if not self.x_planeamento_line_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': 'Planeamento',
            'res_model': 'pg.planeamento.line',
            'res_id': self.x_planeamento_line_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
