from odoo import models, fields, api

class StockMove(models.Model):
    _inherit = 'stock.move'

    depth = fields.Float(string='D', store=True)
    width = fields.Float(string='W', store=True)
    height = fields.Float(string='H', store=True)
    netWeight = fields.Float(string='Net Weight', store=True, readonly=False)
    grossWeight = fields.Float(string='Gross Weight', store=True, readonly=False)
    volume_cbm = fields.Float(string='Volume CBM', compute='_compute_volume_m3', store=True)
    vol = fields.Float(string='Packages Qty', store=True)
    
    # Related Fields from product.template
    x_studio_descricao_m = fields.Char(
        string="Dimensions(cm)/Unit",
        related="product_id.product_tmpl_id.x_studio_dimenses",
        store=True
    )

    x_studio_hs_code = fields.Char(
        string="HS Code",
        related="product_id.product_tmpl_id.hs_code",
        store=True
    )

    @api.depends('depth', 'width', 'height', 'product_uom_qty')
    def _compute_volume_m3(self):
        for move in self:
            move.volume_cbm = (move.depth * move.width * move.height * move.product_uom_qty)



class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    depth = fields.Float(string='D', compute='_compute_from_move', store=True)
    width = fields.Float(string='W', compute='_compute_from_move', store=True)
    height = fields.Float(string='H', compute='_compute_from_move', store=True)
    netWeight = fields.Float(string='Net Weight', compute='_compute_from_move', store=True)
    grossWeight = fields.Float(string='Gross Weight', compute='_compute_from_move', store=True)
    volume_cbm = fields.Float(string='Volume CBM', compute='_compute_volume_m3', store=True)
    vol = fields.Float(string='Packages Qty', compute='_compute_from_move', store=True)

    # Adding Custom Studio Fields
    x_studio_descricao_m = fields.Char(string="Dimensions (cm)/Unit", compute='_compute_from_move', store=True)
    x_studio_hs_code = fields.Char(string="HS Code", compute='_compute_from_move', store=True)

    @api.depends('move_id')
    def _compute_from_move(self):
        for line in self:
            line.depth = line.move_id.depth
            line.width = line.move_id.width
            line.height = line.move_id.height
            line.netWeight = line.move_id.netWeight
            line.grossWeight = line.move_id.grossWeight
            line.vol = line.move_id.vol
            line.x_studio_descricao_m = line.move_id.x_studio_descricao_m  # Copy from move
            line.x_studio_hs_code = line.move_id.x_studio_hs_code  # Copy from move

    @api.depends('depth', 'width', 'height', 'move_id.product_uom_qty')
    def _compute_volume_m3(self):
        for line in self:
            line.volume_cbm = line.depth * line.width * line.height * line.move_id.product_uom_qty

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    total_depth = fields.Float(string='D', compute='_compute_totals', store=True)
    total_width = fields.Float(string='W', compute='_compute_totals', store=True)
    total_height = fields.Float(string='H', compute='_compute_totals', store=True)
    total_netWeight = fields.Float(string='Net Weight', compute='_compute_totals', store=True)
    total_grossWeight = fields.Float(string='Gross Weight', compute='_compute_totals', store=True)
    total_volume_cbm = fields.Float(string='Volume CBM', compute='_compute_totals', store=True)
    total_vol = fields.Float(string='Total Packages', compute='_compute_totals', store=True)

    # Aggregated Studio Fields
    total_x_studio_descricao_m = fields.Char(string="Dimensions (cm)/Unit", compute='_compute_totals', store=True)
    total_x_studio_hs_code = fields.Char(string="Total HS Code", compute='_compute_totals', store=True)

    @api.depends('move_ids_without_package')
    def _compute_totals(self):
        for picking in self:
            picking.total_depth = sum(move.depth for move in picking.move_ids_without_package)
            picking.total_width = sum(move.width for move in picking.move_ids_without_package)
            picking.total_height = sum(move.height for move in picking.move_ids_without_package)
            picking.total_netWeight = sum(move.netWeight for move in picking.move_ids_without_package)
            picking.total_grossWeight = sum(move.grossWeight for move in picking.move_ids_without_package)
            picking.total_volume_cbm = sum(move.volume_cbm for move in picking.move_ids_without_package)
            picking.total_vol = sum(move.vol for move in picking.move_ids_without_package)

            # Combine HS Codes and Descriptions (separated by commas)
            picking.total_x_studio_descricao_m = ", ".join(set(move.x_studio_descricao_m for move in picking.move_ids_without_package if move.x_studio_descricao_m))
            picking.total_x_studio_hs_code = ", ".join(set(move.x_studio_hs_code for move in picking.move_ids_without_package if move.x_studio_hs_code))

