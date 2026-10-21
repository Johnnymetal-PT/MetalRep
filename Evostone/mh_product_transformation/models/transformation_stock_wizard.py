from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class TransformationStockWizard(models.TransientModel):
    _name = 'transformation.stock.wizard'
    _description = 'Wizard de Seleção de Estoque para Transformação'

    transformation_id = fields.Many2one(
        'transformation.document',
        string='Documento de Transformação',
        required=True,
        readonly=True
    )

    location_id = fields.Many2one(
        'stock.location',
        string='Localização',
        related='transformation_id.location_origin_id',
        readonly=True
    )

    product_ids = fields.Many2many(
        'product.product',
        string='Filtrar Produtos',
        domain="[('can_be_transformed', '=', True), ('product_form', 'in', ['block', 'slab', 'strip'])]",
        help='Filtrar apenas produtos específicos (deixe vazio para todos)'
    )

    group_by = fields.Selection([
        ('product_lot', 'Produto + Lote'),
        ('base_lot_name', 'Nome Base do Lote'),
        ('product', 'Produto'),
    ], string='Agrupar Por', default='product_lot', required=True)

    line_ids = fields.One2many(
        'transformation.stock.wizard.line',
        'wizard_id',
        string='Linhas de Estoque'
    )

    @api.onchange('product_ids', 'group_by')
    def _onchange_filters(self):
        """Recalcula linhas quando filtros mudam"""
        self._compute_available_stock()

    def _compute_available_stock(self):
        """Busca e agrupa estoque disponível"""
        self.line_ids = [(5, 0, 0)]  # Limpar linhas existentes

        if not self.location_id:
            return

        # Construir domínio base
        domain = [
            ('location_id', '=', self.location_id.id),
            ('available_quantity', '>', 0),
            ('product_id.can_be_transformed', '=', True),
            ('product_id.product_form', 'in', ['block', 'slab', 'strip'])
        ]

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
            if self.group_by == 'product_lot':
                key = (quant.product_id.id, quant.lot_id.id or False)
            elif self.group_by == 'base_lot_name':
                base_lot_name = quant.lot_id.base_lot_name if quant.lot_id and hasattr(quant.lot_id, 'base_lot_name') else ''
                key = (base_lot_name, quant.product_id.id, quant.lot_id.id or False)
            else:  # product
                key = (quant.product_id.id, quant.lot_id.id or False)

            if key not in grouped_data:
                # Determinar preço de custo (Standard_price)
                preco_custo = 0.0
                if quant.lot_id:
                    preco_custo = quant.lot_id.standard_price or 0.0
                if not preco_custo:
                    preco_custo = quant.product_id.standard_price or 0.0

                grouped_data[key] = {
                    'product_id': quant.product_id.id,
                    'lot_id': quant.lot_id.id if quant.lot_id else False,
                    'location_id': quant.location_id.id,
                    'base_lot_name': quant.lot_id.base_lot_name if quant.lot_id and hasattr(quant.lot_id, 'base_lot_name') else '',
                    'length': quant.length or 0.0,
                    'width': quant.width or 0.0,
                    'thickness': quant.thickness or 0.0,
                    'on_hand_qty': 0.0,
                    'available_qty': 0.0,
                    'units_qty': 0,
                    'units_on_hand': 0,
                    'product_form': quant.product_id.product_form if hasattr(quant.product_id, 'product_form') else 'none',
                    'preco_custo': preco_custo,
                    'quant_ids': [],  # Guardar IDs dos quants para referência
                }

            # Somar quantidade física total (Em Mão)
            grouped_data[key]['on_hand_qty'] += quant.quantity
            # Somar quantidade disponível (Disponível)
            grouped_data[key]['available_qty'] += quant.available_quantity
            # Contar unidades disponíveis
            if hasattr(quant, 'units_qty'):
                grouped_data[key]['units_qty'] += quant.units_qty
            # Contar unidades Em Mão
            if hasattr(quant, 'units_on_hand'):
                grouped_data[key]['units_on_hand'] += quant.units_on_hand
            # Guardar ID do quant
            grouped_data[key]['quant_ids'].append(quant.id)

        # Criar linhas do wizard
        line_vals = []
        for data in grouped_data.values():
            if data['available_qty'] > 0:
                # Pegar o primeiro quant como referência
                quant_id = data['quant_ids'][0] if data['quant_ids'] else False

                line_vals.append((0, 0, {
                    'wizard_id': self.id,
                    'product_id': data['product_id'],
                    'lot_id': data['lot_id'],
                    'location_id': data['location_id'],
                    'base_lot_name': data['base_lot_name'],
                    'length': data['length'],
                    'width': data['width'],
                    'thickness': data['thickness'],
                    'on_hand_qty': data['on_hand_qty'],
                    'available_qty': data['available_qty'],
                    'units_qty': data['units_qty'],
                    'units_on_hand': data['units_on_hand'],
                    'product_form': data['product_form'],
                    'preco_custo': data['preco_custo'],
                    'quant_id': quant_id,
                }))

        self.line_ids = line_vals

    def action_add_selected(self, selected_lines=None):
        """Adiciona linhas selecionadas ao documento de transformação

        Args:
            selected_lines: linhas selecionadas (quando chamado da list view)
        """
        self.ensure_one()

        if not self.transformation_id:
            raise UserError(_('Documento de transformação não encontrado.'))

        # Se não passou linhas, significa que não tem nada selecionado
        if not selected_lines:
            raise UserError(_('Nenhuma linha selecionada.'))

        # Filtrar apenas linhas com quantidade disponível
        lines_to_add = selected_lines.filtered(lambda l: l.available_qty > 0)

        if not lines_to_add:
            raise UserError(_('As linhas selecionadas não têm quantidade disponível.'))

        # Criar linhas no documento de transformação
        input_lines = []
        _logger.info("="*80)
        _logger.info("WIZARD - Adicionando %s linha(s) ao documento %s", len(lines_to_add), self.transformation_id.name)
        _logger.info("="*80)

        for line in lines_to_add:
            _logger.info("-"*40)
            _logger.info("Preparando linha:")
            _logger.info("  Produto: %s", line.product_id.display_name)
            _logger.info("  Lote: %s", line.lot_id.name if line.lot_id else "N/A")
            _logger.info("  Quantidade: %s", line.available_qty)
            _logger.info("  Forma: %s", line.product_form)

            input_line_vals = {
                'transformation_id': self.transformation_id.id,
                'product_id': line.product_id.id,
                'quantity': line.available_qty,
            }

            # Adicionar lote se existir
            if line.lot_id:
                input_line_vals['lot_id'] = line.lot_id.id

            # Adicionar referência ao quant
            if line.quant_id:
                input_line_vals['quant_id'] = line.quant_id.id

            # Adicionar dimensões se for produto com forma
            if line.product_form in ['block', 'slab', 'strip']:
                _logger.info("  Dimensões sendo adicionadas:")
                _logger.info("    length: %s", line.length)
                _logger.info("    width: %s", line.width)
                _logger.info("    thickness: %s", line.thickness)
                _logger.info("    units_qty: %s", line.units_qty or 1)

                # preco_custo NÃO é passado — é computed na linha de input
                # (PCMP do base.lot.group via price_group do lote).
                input_line_vals.update({
                    'length': line.length,
                    'width': line.width,
                    'thickness': line.thickness,
                    'units_qty': line.units_qty or 1,
                })

            _logger.info("  input_line_vals final: %s", input_line_vals)
            input_lines.append((0, 0, input_line_vals))

        if input_lines:
            _logger.info("Gravando %s linha(s) no documento de transformação", len(input_lines))
            self.transformation_id.write({'input_line_ids': input_lines})
            _logger.info("Linhas gravadas com sucesso!")

        _logger.info("="*80)

        return {'type': 'ir.actions.act_window_close'}
