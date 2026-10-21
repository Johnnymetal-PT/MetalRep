from odoo import api, fields, models, _
from odoo.exceptions import UserError


class TransformationStockWizardLine(models.TransientModel):
    _name = 'transformation.stock.wizard.line'
    _description = 'Linha do Wizard de Estoque para Transformação'
    _order = 'product_id, location_id, lot_id'

    wizard_id = fields.Many2one(
        'transformation.stock.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade'
    )

    product_id = fields.Many2one(
        'product.product',
        string='Produto',
        readonly=True
    )

    lot_id = fields.Many2one(
        'stock.lot',
        string='Lote',
        readonly=True
    )

    location_id = fields.Many2one(
        'stock.location',
        string='Localização',
        readonly=True
    )

    base_lot_name = fields.Char(
        string='Nome Base Lote',
        readonly=True
    )

    quant_id = fields.Many2one(
        'stock.quant',
        string='Quant de Referência',
        readonly=True,
        help='Quant de onde virá o estoque'
    )

    length = fields.Float(
        string='Comprimento (m)',
        digits='Dimensions',
        readonly=True
    )

    width = fields.Float(
        string='Largura (m)',
        digits='Dimensions',
        readonly=True
    )

    thickness = fields.Float(
        string='Espessura (m)',
        digits='Dimensions',
        readonly=True
    )

    on_hand_qty = fields.Float(
        string='Em Mão',
        digits='Product Unit of Measure',
        readonly=True,
        help='Quantidade física total em estoque'
    )

    available_qty = fields.Float(
        string='Disponível',
        digits='Product Unit of Measure',
        readonly=True,
        help='Quantidade disponível para transformação (Em Mão - Reservado)'
    )

    product_form = fields.Selection([
        ('none', 'Nenhuma'),
        ('block', 'Bloco'),
        ('slab', 'Placa'),
    ], string='Forma', readonly=True)

    preco_custo = fields.Float(
        string='Preço de Custo',
        digits='Product Price',
        readonly=True,
        help='PCMP ou preço padrão do produto'
    )

    product_uom = fields.Many2one(
        'uom.uom',
        string='Unidade',
        related='product_id.uom_id',
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

    def action_add_selected_lines(self):
        """Adicionar linhas selecionadas ao documento de transformação (chamado da list view)"""
        # self contém as linhas selecionadas da list view
        if not self:
            raise UserError(_('Nenhuma linha selecionada.'))

        # Pegar o wizard do primeiro registro
        wizard = self[0].wizard_id
        if not wizard:
            raise UserError(_('Wizard não encontrado.'))

        # Passar as linhas selecionadas (self) para o método do wizard
        return wizard.action_add_selected(selected_lines=self)
