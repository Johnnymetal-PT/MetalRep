from odoo import api, fields, models


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    # Dimensões do Quant (peça individual)
    length = fields.Float(
        string='Comprimento',
        digits='Dimensions',
        help='Comprimento específico desta peça em metros'
    )
    width = fields.Float(
        string='Largura',
        digits='Dimensions',
        help='Largura específica desta peça em metros'
    )
    thickness = fields.Float(
        string='Espessura',
        digits='Dimensions',
        help='Espessura específica desta peça em metros'
    )

    units_qty = fields.Integer(
        string='Unidades Disponíveis',
        compute='_compute_units_qty',
        store=True,
        aggregator='sum',
        help='Quantidade de unidades/peças disponíveis calculada baseada em available_quantity e dimensões'
    )
    
    units_on_hand = fields.Integer(
        string='Unidades Em Mão',
        compute='_compute_units_qty',
        store=True,
        aggregator='sum',
        help='Quantidade de unidades/peças em mão calculada baseada em quantity e dimensões'
    )

    lot_base_name = fields.Char(
        string='Lot Base Name',
        compute='_compute_lot_base_name',
        store=True,
        help='Nome base do lote para filtragem'
    )

    @api.depends('lot_id', 'lot_id.base_lot_name')
    def _compute_lot_base_name(self):
        """Buscar base_lot_name do lot_id"""
        for quant in self:
            if quant.lot_id and quant.lot_id.base_lot_name:
                quant.lot_base_name = quant.lot_id.base_lot_name
            else:
                quant.lot_base_name = False

    @api.depends('available_quantity', 'quantity', 'product_id.product_form', 'length', 'width', 'thickness')
    def _compute_units_qty(self):
        """Calcula quantidade de unidades baseado em product_form e dimensões

        Para produtos normais (product_form='none'):
        - units_qty = available_quantity (quantidade = unidades)

        Para produtos com forma específica:
        - block: units_qty = available_quantity / (length × width × thickness)
        - slab/strip/tiles: units_qty = available_quantity / (length × width)
        """
        for quant in self:
            if not quant.product_id:
                quant.units_qty = 0
                continue

            product_form = quant.product_id.product_form if hasattr(quant.product_id, 'product_form') else 'none'

            if product_form == 'none':
                # Produtos normais: qty = unidades
                quant.units_qty = round(quant.available_quantity)
                quant.units_on_hand = round(quant.quantity)
            elif product_form == 'block':
                # Volume total / volume unitário
                if quant.length and quant.width and quant.thickness:
                    unit_volume = quant.length * quant.width * quant.thickness
                    quant.units_qty = round(quant.available_quantity / unit_volume) if unit_volume else 0
                    quant.units_on_hand = round(quant.quantity / unit_volume) if unit_volume else 0
                else:
                    quant.units_qty = 0
                    quant.units_on_hand = 0
            elif product_form in ['slab', 'strip', 'tiles']:
                # Área total / área unitária
                if quant.length and quant.width:
                    unit_area = quant.length * quant.width
                    quant.units_qty = round(quant.available_quantity / unit_area) if unit_area else 0
                    quant.units_on_hand = round(quant.quantity / unit_area) if unit_area else 0
                else:
                    quant.units_qty = 0
                    quant.units_on_hand = 0
            else:
                quant.units_qty = 0
                quant.units_on_hand = 0

    @api.model_create_multi
    def create(self, vals_list):
        """Captura dimensões do contexto da move_line"""
        length = self.env.context.get('move_line_length')
        width = self.env.context.get('move_line_width')
        thickness = self.env.context.get('move_line_thickness')

        for vals in vals_list:
            if length and 'length' not in vals:
                vals['length'] = length
            if width and 'width' not in vals:
                vals['width'] = width
            if thickness and 'thickness' not in vals:
                vals['thickness'] = thickness

        return super().create(vals_list)