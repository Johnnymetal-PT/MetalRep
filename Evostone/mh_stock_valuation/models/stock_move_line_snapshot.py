# -*- coding: utf-8 -*-
from odoo import fields, models


class StockMoveLineSnapshot(models.Model):
    """Snapshot do estado de uma stock.move.line ANTES do split por units_qty.

    Capturado no início de stock.picking._split_lines_by_units_qty para
    permitir reconstituir o estado pretendido pelo user (units_qty original,
    qty agregada, dimensões) caso seja necessário investigar diferenças
    entre o pretendido e o resultado final do split.
    """
    _name = 'stock.move.line.snapshot'
    _description = 'Snapshot Pré-Split de Stock Move Line'
    _order = 'create_date desc, id desc'

    move_id = fields.Many2one(
        'stock.move',
        string='Movimento',
        required=True,
        ondelete='cascade',
        index=True,
    )
    picking_id = fields.Many2one(
        'stock.picking',
        related='move_id.picking_id',
        store=True,
        index=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Artigo',
        required=True,
    )
    units_qty = fields.Integer(
        string='Unidades (original)',
        help='Valor de units_qty da move_line antes do split.',
    )
    quantity = fields.Float(
        string='Quantidade Total',
        digits='Product Unit of Measure',
    )
    length = fields.Float(string='Comprimento', digits='Dimensions')
    width = fields.Float(string='Largura', digits='Dimensions')
    thickness = fields.Float(string='Espessura', digits='Dimensions')
    lot_name_base = fields.Char(
        string='Nome Base do Lote',
        help='lot_name do stock.move pretendido (base_lot_name).',
    )
    notes = fields.Text(string='Notas')
