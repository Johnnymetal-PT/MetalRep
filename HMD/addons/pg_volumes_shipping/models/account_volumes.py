from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    total_volume_by_qty = fields.Float(
        string='Volume Total (m³)', 
        compute='_compute_totals', 
        store=True, 
        readonly=False
    )
    total_weight_by_qty = fields.Float(
        string='Peso Total (kg)', 
        compute='_compute_totals', 
        store=True, 
        readonly=False
    )
    total_volume_qty_by_qty = fields.Float(
        string='Volumes', 
        compute='_compute_totals', 
        store=True, 
        readonly=False
    )

    peso_cada_volume = fields.Char(
        string='Peso Cada Volume',
        related='move_ids_without_package.peso_cada_volume',
        readonly=True,
        store=True,
        default="0.0"
    )

    @api.depends(
        'move_ids_without_package.product_volume_by_qty', 
        'move_ids_without_package.product_weight_by_qty', 
        'move_ids_without_package.product_volume_qty_by_qty'
    )
    def _compute_totals(self):
        for picking in self:
            _logger.info(f"Calculating totals for picking: {picking.id}")
            _logger.info(f"Product Volumes: {picking.move_ids_without_package.mapped('product_volume_by_qty')}")
            _logger.info(f"Product Weights: {picking.move_ids_without_package.mapped('product_weight_by_qty')}")
            picking.total_volume_by_qty = sum(move.product_volume_by_qty or 0.0 for move in picking.move_ids_without_package)
            picking.total_weight_by_qty = sum(move.product_weight_by_qty or 0.0 for move in picking.move_ids_without_package)
            picking.total_volume_qty_by_qty = sum(move.product_volume_qty_by_qty or 0.0 for move in picking.move_ids_without_package)


class StockMove(models.Model):
    _inherit = 'stock.move'

    product_volume = fields.Float(
        string='Volume (m³)', 
        related='product_id.volume', 
        readonly=False
    )
    product_weight = fields.Float(
        string='Peso (Kg)', 
        related='product_id.weight', 
        readonly=False
    )
    product_volume_qty = fields.Float(
        string='Volumes', 
        related='product_id.volume_qty', 
        readonly=False
    )

    product_volume_by_qty = fields.Float(
        string='Volume (m³)', 
        compute='_compute_volume_by_qty', 
        store=True, 
        readonly=False
    )
    product_weight_by_qty = fields.Float(
        string='Peso (Kg)', 
        compute='_compute_volume_by_qty', 
        store=True, 
        readonly=False
    )
    product_volume_qty_by_qty = fields.Float(
        string='Volumes', 
        compute='_compute_volume_by_qty', 
        store=True, 
        readonly=False
    )

    peso_cada_volume = fields.Char(
        related='product_id.product_tmpl_id.peso_cada_volume',
        string="Peso Cada Volume",
        readonly=True,
        store=True,
        default="0.0"
    )

    @api.depends(
        'product_uom_qty', 
        'product_volume', 
        'product_weight', 
        'product_volume_qty', 
        'peso_cada_volume'
    )
    def _compute_volume_by_qty(self):
        for move in self:
            _logger.info(f"Calculating volume for move: {move.id}")
            move.product_volume_by_qty = move.product_uom_qty * (move.product_volume or 0.0)
            move.product_weight_by_qty = move.product_uom_qty * (move.product_weight or 0.0)
            move.product_volume_qty_by_qty = move.product_uom_qty * (move.product_volume_qty or 0.0)


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    peso_cada_volume = fields.Char(
        string='Peso Cada Volume', 
        related='move_id.peso_cada_volume', 
        readonly=True
    )

    def _get_aggregated_product_quantities(self, **kwargs):
        """Aggregate product quantities and include additional fields for weight and volume."""
        aggregated_move_lines = super(StockMoveLine, self)._get_aggregated_product_quantities(**kwargs)

        for aggregated_move_line_key, line_data in aggregated_move_lines.items():
            move = line_data.get('move', None)  # Ensure 'move' is in line_data

            if move:
                quantity = line_data.get('quantity', 0.0)
                _logger.info(f"Aggregating product quantities for move: {move.id}")

                # Add custom aggregated fields
                line_data['product_volume_by_qty_list'] = [
                    move.product_volume_by_qty * quantity] if move.product_volume_by_qty else [0.0]
                line_data['product_weight_by_qty_list'] = [
                    move.product_weight_by_qty * quantity] if move.product_weight_by_qty else [0.0]
                line_data['product_volume_qty_by_qty_list'] = [
                    move.product_volume_qty_by_qty * quantity] if move.product_volume_qty_by_qty else [0.0]
                line_data['peso_cada_volume_list'] = [
                    move.peso_cada_volume] if move.peso_cada_volume else ['0.0']

        return aggregated_move_lines

