from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockScrapSelectWizard(models.TransientModel):
    _name = 'stock.scrap.select.wizard'
    _description = 'Wizard de Seleção de Stock para Scrap'

    scrap_id = fields.Many2one(
        'stock.scrap',
        string='Scrap',
        required=True,
        readonly=True
    )

    location_id = fields.Many2one(
        'stock.location',
        string='Localização',
        required=True,
        readonly=True,
        help='Localização de origem do stock'
    )

    line_ids = fields.One2many(
        'stock.scrap.select.wizard.line',
        'wizard_id',
        string='Stock Disponível'
    )

    @api.model
    def default_get(self, fields_list):
        """Carregar dados iniciais do scrap"""
        res = super().default_get(fields_list)

        scrap_id = self.env.context.get('default_scrap_id')
        if scrap_id:
            scrap = self.env['stock.scrap'].browse(scrap_id)
            if scrap.location_id:
                res['location_id'] = scrap.location_id.id

        return res

    def open(self):
        """Abrir wizard e carregar stock disponível"""
        self.ensure_one()
        self._load_available_stock()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Selecionar Stock para Descarte',
            'res_model': 'stock.scrap.select.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _load_available_stock(self):
        """Carregar stock disponível da localização"""
        self.line_ids = [(5, 0, 0)]  # Limpar linhas

        if not self.location_id:
            return

        # Buscar quants disponíveis
        domain = [
            ('location_id', '=', self.location_id.id),
            ('quantity', '>', 0),
        ]

        quants = self.env['stock.quant'].search(domain)

        if not quants:
            return

        # Criar linhas
        line_vals = []
        for quant in quants:
            available_qty = quant.quantity - quant.reserved_quantity

            if available_qty > 0:
                vals = {
                    'wizard_id': self.id,
                    'quant_id': quant.id,
                    'product_id': quant.product_id.id,
                    'lot_id': quant.lot_id.id if quant.lot_id else False,
                    'location_id': quant.location_id.id,
                    'on_hand_qty': quant.quantity,
                    'available_qty': available_qty,
                    'length': quant.length if hasattr(quant, 'length') else 0.0,
                    'width': quant.width if hasattr(quant, 'width') else 0.0,
                    'thickness': quant.thickness if hasattr(quant, 'thickness') else 0.0,
                    'units_qty': quant.units_qty if hasattr(quant, 'units_qty') else 0,
                    'units_on_hand': quant.units_on_hand if hasattr(quant, 'units_on_hand') else 0,
                    'base_lot_name': quant.lot_id.base_lot_name if quant.lot_id and hasattr(quant.lot_id, 'base_lot_name') else '',
                    'price_group_id': quant.lot_id.sudo().price_group_id.id if quant.lot_id and hasattr(quant.lot_id, 'price_group_id') and quant.lot_id.sudo().price_group_id else False,
                    'product_form': quant.product_id.product_form if hasattr(quant.product_id, 'product_form') else 'none',
                }

                # Obter preço do lote ou produto
                if quant.lot_id and hasattr(quant.lot_id, 'list_price_lot'):
                    vals['list_price'] = quant.lot_id.list_price_lot
                else:
                    vals['list_price'] = quant.product_id.list_price

                line_vals.append((0, 0, vals))

        self.line_ids = line_vals

    def action_refresh(self):
        """Atualizar lista de stock"""
        self._load_available_stock()
        return self.open()

    def action_select_quant(self):
        """Selecionar quant (chamado da tree view)"""
        # Este método será chamado quando usuário clicar na linha
        # O JS vai chamar action_apply_selection com o quant_id
        return True


class StockScrapSelectWizardLine(models.TransientModel):
    _name = 'stock.scrap.select.wizard.line'
    _description = 'Linha do Wizard de Seleção de Stock para Scrap'
    _order = 'product_id, lot_id'

    wizard_id = fields.Many2one(
        'stock.scrap.select.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade'
    )

    quant_id = fields.Many2one(
        'stock.quant',
        string='Quant',
        required=True,
        readonly=True
    )

    product_id = fields.Many2one(
        'product.product',
        string='Produto',
        readonly=True
    )

    lot_id = fields.Many2one(
        'stock.lot',
        string='SN',
        readonly=True
    )

    location_id = fields.Many2one(
        'stock.location',
        string='Localização',
        readonly=True
    )

    on_hand_qty = fields.Float(
        string='Em Mão',
        digits='Product Unit of Measure',
        readonly=True
    )

    available_qty = fields.Float(
        string='Disponível',
        digits='Product Unit of Measure',
        readonly=True
    )

    length = fields.Float(
        string='Comprimento',
        digits='Dimensions',
        readonly=True
    )

    width = fields.Float(
        string='Largura',
        digits='Dimensions',
        readonly=True
    )

    thickness = fields.Float(
        string='Espessura',
        digits='Dimensions',
        readonly=True
    )

    units_qty = fields.Integer(
        string='Uni. Disponível',
        readonly=True,
        help='Quantidade de unidades (peças) Disponíveis'
    )

    units_on_hand = fields.Integer(
        string='Uni. Em Mão',
        readonly=True,
        help='Quantidade de unidades (peças) Em Mão'
    )

    list_price = fields.Float(
        string='Preço',
        digits='Product Price',
        readonly=True
    )

    product_uom = fields.Many2one(
        'uom.uom',
        string='Unidade',
        related='product_id.uom_id',
        readonly=True
    )

    base_lot_name = fields.Char(
        string='Grupo de Lote',
        readonly=True
    )

    price_group_id = fields.Many2one(
        'lot.price.group',
        string='Grupo Dimensões',
        readonly=True
    )

    product_form = fields.Selection([
        ('none', 'Nenhum'),
        ('block', 'Bloco'),
        ('slab', 'Placa'),
        ('strip', 'Banda'),
        ('tiles', 'Ladrilhos'),
    ], string='Forma', readonly=True)

    stock_state = fields.Selection([
        ('available', 'Disponível'),
        ('reserved', 'Reservado'),
        ('unavailable', 'Indisponível')
    ], string='Estado do Stock', compute='_compute_stock_state', store=True, readonly=True)

    @api.depends('units_on_hand', 'units_qty')
    def _compute_stock_state(self):
        """Determina estado do stock baseado em unidades em mão vs disponíveis"""
        for line in self:
            if line.units_on_hand > 0:
                if line.units_qty > 0:
                    # Tem stock físico e está disponível
                    line.stock_state = 'available'
                else:
                    # Tem stock físico mas todo reservado/comprometido
                    line.stock_state = 'reserved'
            else:
                # Não tem stock físico
                line.stock_state = 'unavailable'

    def action_apply_selection(self):
        """Aplicar quant selecionado ao scrap"""
        self.ensure_one()

        wizard = self.wizard_id
        scrap = wizard.scrap_id

        if not scrap:
            raise UserError(_('Scrap não encontrado.'))

        # Atualizar scrap com dados do quant
        # Inclui valores congelados dos campos do quant para não mudarem posteriormente
        scrap.write({
            'product_id': self.product_id.id,
            'lot_id': self.lot_id.id if self.lot_id else False,
            'scrap_qty': self.available_qty,
            'selected_quant_id': self.quant_id.id,
            # Campos congelados - valores do momento da seleção
            'quant_location_id': self.location_id.id,
            'quant_on_hand': self.on_hand_qty,
            'quant_available': self.available_qty,
            'quant_length': self.length,
            'quant_width': self.width,
            'quant_thickness': self.thickness,
            'quant_units': self.units_qty,
        })

        return {'type': 'ir.actions.act_window_close'}
