from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class StockAvailableWizard(models.TransientModel):
    _name = 'stock.available.wizard'
    _description = 'Wizard de Seleção de Estoque Disponível'

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Ordem de Venda',
        required=True,
        readonly=True
    )

    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Armazém',
        help='Filtrar estoque por armazém específico'
    )

    product_ids = fields.Many2many(
        'product.product',
        string='Filtrar Produtos',
        domain="[('product_form', 'in', ['block', 'slab', 'strip', 'tiles'])]",
        help='Filtrar apenas produtos específicos (deixe vazio para todos)'
    )

    group_by = fields.Selection([
        ('location_product', 'Localização + Produto'),
        ('base_lot_name', 'Nome Base do Lote'),
        ('price_group', 'Grupo de Preço'),
    ], string='Agrupar Por', default='location_product', required=True)

    line_ids = fields.One2many(
        'stock.available.wizard.line',
        'wizard_id',
        string='Linhas de Estoque'
    )

    @api.onchange('warehouse_id', 'product_ids', 'group_by')
    def _onchange_filters(self):
        """Recalcula linhas quando filtros mudam"""
        self._compute_available_stock()

    def _compute_available_stock(self):
        """Busca e agrupa estoque disponível"""
        self.line_ids = [(5, 0, 0)]  # Limpar linhas existentes

        # Construir domínio base
        domain = [
            ('location_id.usage', '=', 'internal'),
            ('quantity', '>', 0),
            ('product_id.product_form', 'in', ['block', 'slab', 'strip', 'tiles'])
        ]

        # Filtro por armazém
        if self.warehouse_id:
            domain.append(('location_id.warehouse_id', '=', self.warehouse_id.id))
        elif self.sale_order_id.warehouse_id:
            domain.append(('location_id.warehouse_id', '=', self.sale_order_id.warehouse_id.id))

        # Filtro por produtos
        if self.product_ids:
            domain.append(('product_id', 'in', self.product_ids.ids))

        # Buscar quants
        quants = self.env['stock.quant'].search(domain)

        if not quants:
            return

        # Agrupar conforme seleção
        grouped_data = {}

        for quant in quants:
            # Definir chave de agrupamento
            if self.group_by == 'location_product':
                key = (quant.location_id.id, quant.product_id.id, quant.lot_id.id or False)
            elif self.group_by == 'base_lot_name':
                base_lot_name = quant.lot_id.base_lot_name if quant.lot_id and hasattr(quant.lot_id, 'base_lot_name') else ''
                key = (base_lot_name, quant.product_id.id, quant.lot_id.id or False)
            else:  # price_group
                price_group_id = quant.lot_id.sudo().price_group_id.id if quant.lot_id and hasattr(quant.lot_id, 'price_group_id') and quant.lot_id.sudo().price_group_id else False
                key = (price_group_id, quant.product_id.id, quant.lot_id.id or False)

            if key not in grouped_data:
                grouped_data[key] = {
                    'product_id': quant.product_id.id,
                    'lot_id': quant.lot_id.id if quant.lot_id else False,
                    'location_id': quant.location_id.id,
                    'base_lot_name': quant.lot_id.base_lot_name if quant.lot_id and hasattr(quant.lot_id, 'base_lot_name') else '',
                    'price_group_id': quant.lot_id.sudo().price_group_id.id if quant.lot_id and hasattr(quant.lot_id, 'price_group_id') and quant.lot_id.sudo().price_group_id else False,
                    'length': quant.length or 0.0,
                    'width': quant.width or 0.0,
                    'thickness': quant.thickness or 0.0,
                    'on_hand_qty': 0.0,
                    'available_qty': 0.0,
                    'units_qty': 0,
                    'units_on_hand': 0,
                    'product_form': quant.product_id.product_form if hasattr(quant.product_id, 'product_form') else 'none',
                    'list_price': quant.lot_id.list_price_lot if (quant.lot_id and hasattr(quant.lot_id, 'list_price_lot') and self.sale_order_id._mh_stone_gates_apply()) else quant.product_id.list_price,
                }

            # Somar quantidade física total (Em Mão)
            grouped_data[key]['on_hand_qty'] += quant.quantity
            # Somar quantidade disponível (Disponível)
            grouped_data[key]['available_qty'] += quant.available_quantity
            # Contar unidades disponíveis (baseado em available_quantity)
            grouped_data[key]['units_qty'] += quant.units_qty
            # Contar unidades Em Mão (baseado em quantity, não em available_quantity)
            grouped_data[key]['units_on_hand'] += quant.units_on_hand

        # Criar linhas do wizard
        line_vals = []
        for data in grouped_data.values():
            if data['on_hand_qty'] > 0:
                line_vals.append((0, 0, {
                    'wizard_id': self.id,
                    **data
                }))

        self.line_ids = line_vals

    def action_refresh(self):
        """Atualiza lista de estoque disponível"""
        self._compute_available_stock()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.available.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_add_selected(self, selected_lines=None):
        """Adiciona linhas selecionadas à ordem de venda

        Args:
            selected_lines: linhas selecionadas (quando chamado da list view)
        """
        self.ensure_one()

        if not self.sale_order_id:
            raise UserError(_('Ordem de venda não encontrada.'))

        # Se não passou linhas, significa que não tem nada selecionado
        if not selected_lines:
            raise UserError(_('Nenhuma linha selecionada.'))

        # Filtrar apenas linhas com quantidade disponível
        lines_to_add = selected_lines.filtered(lambda l: l.available_qty > 0)

        if not lines_to_add:
            raise UserError(_('As linhas selecionadas não têm quantidade disponível.'))

        # Criar linhas na ordem de venda
        order_lines = []
        _logger.warning("="*80)
        _logger.warning("WIZARD - Adicionando %s linha(s) à ordem %s", len(lines_to_add), self.sale_order_id.name)
        _logger.warning("="*80)

        for line in lines_to_add:
            _logger.warning("-"*40)
            _logger.warning("Preparando linha:")
            _logger.warning("  Produto: %s", line.product_id.display_name)
            _logger.warning("  Lote: %s", line.lot_id.name if line.lot_id else "N/A")
            _logger.warning("  Quantidade: %s", line.available_qty)
            _logger.warning("  Forma: %s", line.product_form)

            order_line_vals = {
                'order_id': self.sale_order_id.id,
                'product_id': line.product_id.id,
                'product_uom_qty': line.available_qty,
            }

            # Adicionar lote se existir e forçar preço do lote
            if line.lot_id:
                order_line_vals['lot_id'] = line.lot_id.id
                # Forçar preço do lote apenas no fluxo stone (Moçambique)
                if hasattr(line.lot_id, 'list_price_lot') and self.sale_order_id._mh_stone_gates_apply():
                    order_line_vals['price_unit'] = line.lot_id.list_price_lot
                else:
                    order_line_vals['price_unit'] = line.product_id.lst_price

            # Adicionar dimensões se for produto com forma
            if line.product_form in ['block', 'slab', 'strip', 'tiles']:
                _logger.warning("  Dimensões sendo adicionadas:")
                _logger.warning("    length: %s", line.length)
                _logger.warning("    width: %s", line.width)
                _logger.warning("    thickness: %s", line.thickness)
                _logger.warning("    units_qty: %s", line.units_qty or 1)

                order_line_vals.update({
                    'length': line.length,
                    'width': line.width,
                    'thickness': line.thickness,
                    'units_qty': line.units_qty or 1,  # Usar units_qty do wizard line ou 1 como padrão
                })

            _logger.warning("  order_line_vals final: %s", order_line_vals)
            order_lines.append((0, 0, order_line_vals))

        if order_lines:
            _logger.warning("Gravando %s linha(s) na ordem de venda", len(order_lines))
            self.sale_order_id.write({'order_line': order_lines})
            _logger.warning("Linhas gravadas com sucesso!")

        _logger.warning("="*80)

        return {'type': 'ir.actions.act_window_close'}


class StockAvailableWizardLine(models.TransientModel):
    _name = 'stock.available.wizard.line'
    _description = 'Linha do Wizard de Estoque Disponível'
    _order = 'product_id, location_id'

    wizard_id = fields.Many2one(
        'stock.available.wizard',
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
        string='SN',
        readonly=True
    )

    location_id = fields.Many2one(
        'stock.location',
        string='Localização',
        readonly=True
    )

    base_lot_name = fields.Char(
        string='Grupo de Lote',
        readonly=True
    )

    price_group_id = fields.Many2one(
        'lot.price.group',
        string='Grupo de Dimensões',
        readonly=True
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
        help='Quantidade disponível para venda (Em Mão - Reservado)'
    )

    product_form = fields.Selection([
        ('block', 'Bloco'),
        ('slab', 'Placa'),
        ('strip', 'Banda'),
        ('tiles', 'Ladrilhos'),
    ], string='Forma', readonly=True)

    list_price = fields.Float(
        string='Preço Unitário',
        digits='Product Price',
        readonly=True
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
        """Adicionar linhas selecionadas à ordem de venda (chamado da list view)"""
        # self contém as linhas selecionadas da list view
        if not self:
            raise UserError(_('Nenhuma linha selecionada.'))

        # Pegar o wizard do primeiro registro
        wizard = self[0].wizard_id
        if not wizard:
            raise UserError(_('Wizard não encontrado.'))

        # Passar as linhas selecionadas (self) para o método do wizard
        return wizard.action_add_selected(selected_lines=self)
