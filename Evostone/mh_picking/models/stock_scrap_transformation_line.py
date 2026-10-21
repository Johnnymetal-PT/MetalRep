from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_round


class StockScrapLine(models.Model):
    _name = 'stock.scrap.transformation.line'
    _description = 'Linha de Scrap (Sobra/Nova Placa)'

    scrap_id = fields.Many2one(
        'stock.scrap',
        string='Scrap',
        required=True,
        ondelete='cascade',
    )

    product_id = fields.Many2one(
        'product.product',
        string='Artigo',
        required=True,
        domain="['|', ('id', '=', scrap_product_id), ('product_form', '=', next_product_form)]",
    )

    scrap_product_id = fields.Integer(
        compute='_compute_scrap_product_id',
    )

    next_product_form = fields.Char(
        compute='_compute_next_product_form',
    )

    @api.depends('scrap_id.product_id')
    def _compute_scrap_product_id(self):
        for line in self:
            line.scrap_product_id = line.scrap_id.product_id.id or 0

    @api.depends('scrap_id.product_form')
    def _compute_next_product_form(self):
        NEXT = {
            'block': 'slab',
            'slab': 'strip',
            'strip': 'tiles',
            'tiles': False,
        }
        for line in self:
            line.next_product_form = NEXT.get(line.scrap_id.product_form or 'none', False)

    length = fields.Float(
        string='Comprimento',
        digits='Dimensions',
        required=True,
    )

    width = fields.Float(
        string='Largura',
        digits='Dimensions',
        required=True,
    )

    thickness = fields.Float(
        string='Espessura',
        digits='Dimensions',
        readonly=True,
    )

    area = fields.Float(
        string='Volume/Área',
        digits='Product Unit of Measure',
        compute='_compute_area',
        store=True,
    )

    units_qty = fields.Integer(
        string='Quantidade',
        default=1,
    )

    product_uom_id = fields.Many2one(
        related='product_id.uom_id',
        string='UdM',
        readonly=True,
    )

    lot_name = fields.Char(
        string='Lote',
        compute='_compute_lot_name',
        store=True,
        readonly=False,
        required=True,
    )

    @api.depends('scrap_id.lot_id.code')
    def _compute_lot_name(self):
        for line in self:
            if not line.lot_name and line.scrap_id.lot_id:
                line.lot_name = line.scrap_id.lot_id.code

    price_unit = fields.Float(
        string='Preço Unit.',
        compute='_compute_price_unit',
        digits='Product Price',
    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Herdar espessura do produto seleccionado"""
        if self.product_id and hasattr(self.product_id, 'thickness') and self.product_id.thickness:
            self.thickness = self.product_id.thickness

    @api.depends('scrap_id.lot_id.price_group_id.pcmp')
    def _compute_price_unit(self):
        for line in self:
            scrap = line.scrap_id
            if scrap.lot_id and hasattr(scrap.lot_id, 'price_group_id') and scrap.lot_id.sudo().price_group_id:
                line.price_unit = scrap.lot_id.sudo().price_group_id.pcmp
            else:
                line.price_unit = 0.0

    @api.depends('length', 'width', 'units_qty', 'product_id')
    def _compute_area(self):
        for line in self:
            product_form = line.product_id.product_form if line.product_id and hasattr(line.product_id, 'product_form') else 'none'
            uom_rounding = line.product_id.uom_id.rounding if line.product_id and line.product_id.uom_id else 0.0001
            qty = line.units_qty or 1
            if product_form == 'block':
                if line.length and line.width and line.thickness:
                    line.area = float_round(line.length * line.width * line.thickness * qty, precision_rounding=uom_rounding)
                else:
                    line.area = 0.0
            elif product_form in ('slab', 'strip', 'tiles'):
                if line.length and line.width:
                    line.area = float_round(line.length * line.width * qty, precision_rounding=uom_rounding)
                else:
                    line.area = 0.0
            else:
                line.area = float_round(qty, precision_rounding=uom_rounding)

    @api.constrains('area', 'units_qty')
    def _check_total_area(self):
        for line in self:
            scrap = line.scrap_id
            if scrap and scrap.scrap_qty:
                total_area = sum(l.area for l in scrap.scrap_line_ids)
                if total_area > scrap.scrap_qty:
                    raise ValidationError(
                        'O total das sobras (%.4f) ultrapassa a quantidade original (%.4f).'
                        % (total_area, scrap.scrap_qty)
                    )

    @api.model_create_multi
    def create(self, vals_list):
        """Herdar espessura e produto do scrap pai ao criar linhas"""
        for vals in vals_list:
            if vals.get('scrap_id'):
                scrap = self.env['stock.scrap'].browse(vals['scrap_id'])
                if not vals.get('thickness') and scrap.quant_thickness:
                    vals['thickness'] = scrap.quant_thickness
                if not vals.get('product_id') and scrap.product_id:
                    vals['product_id'] = scrap.product_id.id
        return super().create(vals_list)
