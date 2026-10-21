# -*- coding: utf-8 -*-

from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    """
    Extensão do stock.move para mh_purchase.

    NOTA: A lógica PCMP é controlada pelo mh_stock_valuation.
    Este módulo apenas adiciona campos para rastreabilidade e relações.
    """
    _inherit = 'stock.move'

    # Campos de rastreabilidade
    is_initial_stock = fields.Boolean(
        string='Stock Inicial',
        help='Indica se este movimento é de stock inicial',
        index=True
    )
    import_document_id = fields.Many2one(
        'import.document',
        string='Documento de Importação',
        help='Documento de importação relacionado',
        index=True
    )
    transformation_id = fields.Many2one(
        'transformation.document',
        string='Documento de Transformação',
        help='Documento de transformação relacionado',
        index=True
    )

    # Métodos auxiliares
    def _get_warehouse(self):
        """
        Obtém warehouse de forma segura, tentando várias fontes.

        Returns:
            stock.warehouse: Warehouse encontrado ou False
        """
        # Tentar do próprio movimento
        if self.warehouse_id:
            return self.warehouse_id

        # Tentar do picking
        if self.picking_id and self.picking_id.picking_type_id.warehouse_id:
            return self.picking_id.picking_type_id.warehouse_id

        # Tentar da localização origem
        if self.location_id and self.location_id.warehouse_id:
            return self.location_id.warehouse_id

        # Tentar da localização destino
        if self.location_dest_id and self.location_dest_id.warehouse_id:
            return self.location_dest_id.warehouse_id

        return False

    def _get_lot_for_move(self):
        """
        Obtém o lote associado ao movimento de forma segura.

        Returns:
            stock.lot: Lote encontrado ou False
        """
        # Primeiro tentar do campo lot_id direto (se existir)
        if hasattr(self, 'lot_id') and self.lot_id:
            return self.lot_id

        # Tentar das move lines
        if self.move_line_ids:
            for line in self.move_line_ids:
                if line.lot_id:
                    return line.lot_id

        # Tentar do contexto
        lot_id = self.env.context.get('lot_id')
        if lot_id:
            lot = self.env['stock.lot'].browse(lot_id)
            if lot.exists():
                return lot

        return False

    @api.model_create_multi
    def create(self, vals_list):
        """Override para preencher lot_name automaticamente em vendas"""
        moves = super().create(vals_list)

        # Preencher lot_name a partir de sale_line_id.lot_id se existir
        for move in moves:
            if move.sale_line_id and hasattr(move.sale_line_id, 'lot_id') and move.sale_line_id.lot_id:
                if not move.lot_name:
                    move.lot_name = move.sale_line_id.lot_id.base_lot_name
                    _logger.info(f"Auto-preenchido move.lot_name de venda: {move.lot_name}")

        return moves

    def write(self, vals):
        """Override para preencher lot_name quando sale_line_id é atualizada"""
        result = super().write(vals)

        # Se sale_line_id foi alterada, tentar preencher lot_name
        if 'sale_line_id' in vals:
            for move in self:
                if move.sale_line_id and hasattr(move.sale_line_id, 'lot_id') and move.sale_line_id.lot_id:
                    if not move.lot_name:
                        move.lot_name = move.sale_line_id.lot_id.base_lot_name
                        _logger.info(f"Auto-preenchido move.lot_name de venda: {move.lot_name}")

        return result
