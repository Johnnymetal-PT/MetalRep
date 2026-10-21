from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round
import logging

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = 'stock.move'

    # Campo para nome do lote (usado por PCMP)
    lot_name = fields.Char(
        string='Lote',
        help="Lote para agrupamento PCMP."
    )

    # Dimensões
    length = fields.Float(
        string='Comprimento',
        digits=(10, 3),
        help='Comprimento em metros'
    )
    width = fields.Float(
        string='Largura',
        digits=(10, 3),
        help='Largura em metros'
    )
    thickness = fields.Float(
        string='Espessura',
        digits=(10, 3),
        help='Espessura em metros'
    )

    units_qty = fields.Integer(
        string='Qtd. Unidades',
        default=1,
        help='Número de peças/unidades a serem movimentadas'
    )


    peso = fields.Float(
        string='Peso (kg)',
        compute='_compute_peso',
        store=True,
        digits=(10, 2),
        help='Peso total calculado a partir de quantity (qty efectivamente movimentada):\n'
             '- block: quantity (m³) × densidade\n'
             '- slab/strip/tiles: quantity (m²) × espessura × densidade\n'
             '- none: quantity × product.weight\n'
             'Densidade: product.density ou parâmetro '
             'campo Empresa → Densidade Padrão de Pedra (default 2700 kg/m³).',
    )

    @api.depends('state', 'thickness', 'quantity', 'product_id',
                 'product_id.density', 'product_id.weight', 'product_id.product_form',
                 'company_id.stone_density')
    def _compute_peso(self):
        """Peso por product_form. Quando move está 'done' E peso já tem valor,
        preserva (snapshot histórico — protege de alterações posteriores de
        density/dimensões).
        """
        for move in self:
            if move.state == 'done' and move.peso:
                continue
            default_density = (move.company_id.stone_density
                               if move.company_id else 0) or 2700
            product_form = getattr(move.product_id, 'product_form', 'none')
            qty = move.quantity or 0.0
            if product_form == 'block':
                density = (move.product_id.density if move.product_id else 0) or default_density
                move.peso = qty * density
            elif product_form in ('slab', 'strip', 'tiles'):
                density = (move.product_id.density if move.product_id else 0) or default_density
                move.peso = qty * (move.thickness or 0.0) * density
            else:
                move.peso = qty * (move.product_id.weight or 0)

    product_form = fields.Selection(
        related='product_id.product_form',
        string='Forma do Produto',
        store=True,
        readonly=True
    )

    is_move_readonly = fields.Boolean(
        string='Movimento em Modo Somente Leitura',
        compute='_compute_is_move_readonly',
        help='Indica se o movimento deve ser somente leitura (verdadeiro quando vem de venda ou produto sem forma)'
    )

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        """Adiciona lot_name aos campos distintos para evitar merge de moves

        Moves com lot_name diferentes não serão combinados durante action_confirm.
        Isso permite manter moves separados por lote no mesmo picking.
        """
        distinct_fields = super()._prepare_merge_moves_distinct_fields()
        distinct_fields += ["lot_name", "length", "width", "thickness"]
        return distinct_fields

    @api.depends('sale_line_id')
    def _compute_is_move_readonly(self):
        """Determina se o movimento deve ser readonly

        O movimento é readonly quando:
        - Está vinculado a uma linha de venda (sale_line_id)
        """
        for record in self:
            has_sale_line = bool(record.sale_line_id)
            record.is_move_readonly = has_sale_line

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        """Override para passar dimensões do move para o move_line.

        Nota: move_line.peso é compute (calcula a partir de L×W×T×units×density),
        por isso não passamos peso aqui.
        """
        vals = super()._prepare_move_line_vals(quantity=quantity, reserved_quant=reserved_quant)
        vals.update({
            'length': self.length,
            'width': self.width,
            'thickness': self.thickness,
            'units_qty': self.units_qty,
        })
        return vals


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    # Dimensões (obrigatórias se product_form != 'none')
    # Campos para grupo de lote
    # lot_name = fields.Char(
    #     string='Lote',
    #     help="Lote para valorização PCMP. "
    #          "Copiado da linha de compra.",
    # )
    
    length = fields.Float(
        string='Comprimento',
        digits='Dimensions',
        help='Comprimento em metros'
    )

    width = fields.Float(
        string='Largura',
        digits='Dimensions',
        help='Largura em metros'
    )

    thickness = fields.Float(
        string='Espessura',
        digits='Dimensions',
        help='Espessura em metros'
    )

    product_form = fields.Selection(
        related='product_id.product_form',
        string='Forma do Produto',
        store=True,
        readonly=True
    )

    units_qty = fields.Integer(
        string='Quantidade',
        default=1,
        help='Número de peças/unidades (blocos, placas, bandas ou ladrilhos) a serem recebidas'
    )

    peso = fields.Float(
        string='Peso (kg)',
        compute='_compute_peso',
        store=True,
        digits=(10, 2),
        help='Peso total calculado:\n'
             '- Para produtos dimensionais (block/slab/strip/tiles): '
             'L × W × T × units_qty × densidade\n'
             '- Para produtos sem forma (none): product.weight × quantity\n'
             'Densidade: product.density ou parâmetro '
             'campo Empresa → Densidade Padrão de Pedra (default 2700 kg/m³).',
    )

    @api.depends('state', 'thickness', 'quantity', 'product_id',
                 'product_id.density', 'product_id.weight', 'product_id.product_form',
                 'company_id.stone_density')
    def _compute_peso(self):
        """Peso da move_line. Mesma fórmula do stock.move (usa quantity).
        Quando state='done' E peso já tem valor, preserva (snapshot histórico).
        """
        for line in self:
            if line.state == 'done' and line.peso:
                continue
            default_density = (line.company_id.stone_density
                               if line.company_id else 0) or 2700
            product_form = getattr(line.product_id, 'product_form', 'none')
            qty = line.quantity or 0.0
            if product_form == 'block':
                density = (line.product_id.density if line.product_id else 0) or default_density
                line.peso = qty * density
            elif product_form in ('slab', 'strip', 'tiles'):
                density = (line.product_id.density if line.product_id else 0) or default_density
                line.peso = qty * (line.thickness or 0.0) * density
            else:
                line.peso = qty * (line.product_id.weight or 0)

    is_dimensions_readonly = fields.Boolean(
        string='Dimensões em Modo Somente Leitura',
        compute='_compute_is_dimensions_readonly',
        help='Indica se os campos de dimensões devem ser somente leitura (verdadeiro quando vem de venda com dimensões)'
    )
    
    is_lot_name_readonly = fields.Boolean(
        string='Lote Name em Modo Somente Leitura',
        compute='_compute_is_lot_name_readonly',
        help='Indica se lot_name deve ser somente leitura (verdadeiro quando vem de compra)'
    )

    show_quant_field = fields.Boolean(
        string='Mostrar Campo Quant',
        compute='_compute_show_quant_field',
        help='Indica se o campo quant_id deve ser exibido (quando parent.lot_name existe)'
    )

    # Campos related para acesso em views (evitar uso de parent.*)
    parent_lot_name = fields.Char(
        string='Lote (Move)',
        related='move_id.lot_name',
        readonly=True,
        help='Nome do lote do movimento pai'
    )

    parent_location_id = fields.Many2one(
        'stock.location',
        string='Localização (Move)',
        related='move_id.location_id',
        readonly=True,
        help='Localização do movimento pai'
    )

    @api.onchange('product_id')
    def _onchange_product_id_thickness(self):
        """Preencher thickness automaticamente quando produto é selecionado

        Preenche thickness do produto quando product_form for 'slab', 'strip' ou 'tiles'
        (não preenche para 'none' nem 'block')
        """
        if not self.product_id:
            return

        product_form = self.product_id.product_form if hasattr(self.product_id, 'product_form') else 'none'

        # Preencher thickness apenas se product_form não for 'none' e não for 'block'
        # E apenas se thickness estiver vazio
        if product_form in ['slab', 'strip', 'tiles'] and not self.thickness:
            # Pegar thickness do produto se disponível
            if hasattr(self.product_id, 'thickness') and self.product_id.thickness:
                self.thickness = self.product_id.thickness

    @api.depends('move_id.sale_line_id', 'product_id.product_form')
    def _compute_is_dimensions_readonly(self):
        """Determina se as dimensões devem ser readonly

        As dimensões são readonly quando:
        - O movimento está vinculado a uma linha de venda (sale_line_id)
        """
        for record in self:
            has_sale_line = bool(record.move_id.sale_line_id) if record.move_id else False
            has_form_none = bool(record.product_id.product_form == "none")
            record.is_dimensions_readonly = has_sale_line or has_form_none
    
    @api.depends('move_id.purchase_line_id', 'product_id.product_form', 'package_level_id', 'picking_id.picking_type_id')
    def _compute_is_lot_name_readonly(self):
        """Determina se lot_name deve ser readonly

        Lógica:
        - Se vem de compra (purchase_line_id):
            readonly se (package_level + entire_packs) ou product tem forma física
        - Se NÃO vem de compra:
            editável se product tem forma física (slab, block, etc.)
            readonly se product não tem forma (none)
        """
        for record in self:
            purchase_line_on = bool(record.move_id.purchase_line_id) if record.move_id else False
            product_form = record.product_id.product_form if record.product_id else 'none'

            if purchase_line_on:
                # Vem de compra: readonly baseado em package_level ou forma do produto
                entire_packs = record.picking_id.picking_type_id.show_entire_packs if record.picking_id and record.picking_id.picking_type_id else False
                record.is_lot_name_readonly = (record.package_level_id and entire_packs) or product_form != 'none'
            else:
                # Não vem de compra: editável se tem forma física, readonly se não tem
                record.is_lot_name_readonly = product_form == 'none'

    @api.depends('move_id.lot_name')
    def _compute_show_quant_field(self):
        """Determina se o campo quant_id deve ser exibido

        O campo quant_id deve ser exibido quando o movimento pai tem lot_name definido.
        Isso permite filtrar quants por lot_base_name quando aplicável.
        """
        for line in self:
            line.show_quant_field = bool(line.move_id and line.move_id.lot_name)

    @api.depends('quant_id', 'length', 'width', 'thickness', 'product_id.product_form', 'units_qty')
    def _compute_quantity(self):
        """Sobrescreve método nativo para calcular quantity baseado em dimensões

        Para produtos do tipo block, slab, strip, tiles:
        - quantity = área/volume unitário × quantidade de unidades
        - Usa float_round com precision do UOM (como Odoo nativo)

        Para outros produtos:
        - Mantém comportamento padrão (baseado em quant_id)
        """
        for record in self:
            if not record.product_id:
                continue

            product_form = record.product_id.product_form if hasattr(record.product_id, 'product_form') else 'none'

            # Para produtos com forma específica, calcular quantity baseado em dimensões
            if product_form in ['block', 'slab', 'strip', 'tiles']:
                units_qty = record.units_qty or 1  # Default 1 se vazio

                if product_form == 'block':
                    # Volume total (m³) = comprimento × largura × espessura × unidades
                    if record.length and record.width and record.thickness:
                        calculated = record.length * record.width * record.thickness * units_qty
                        # Arredondar com precision do UOM (como Odoo faz nativamente)
                        record.quantity = float_round(calculated,
                                                     precision_rounding=record.product_uom_id.rounding)
                    else:
                        record.quantity = 0.0
                elif product_form in ['slab', 'strip', 'tiles']:
                    # Área total (m²) = comprimento × largura × unidades
                    if record.length and record.width:
                        calculated = record.length * record.width * units_qty
                        # Arredondar com precision do UOM (como Odoo faz nativamente)
                        record.quantity = float_round(calculated,
                                                     precision_rounding=record.product_uom_id.rounding)
                    else:
                        record.quantity = 0.0
            elif product_form in ['none']:
                record.quantity = float_round(record.units_qty,
                                                     precision_rounding=record.product_uom_id.rounding)
            else:
                # Manter comportamento padrão do Odoo (quant logic)
                super(StockMoveLine, record)._compute_quantity()

    @api.constrains('length', 'width', 'thickness', 'product_id')
    def _check_dimensions(self):
        """Valida que dimensões obrigatórias estão preenchidas"""
        _logger.warning("="*80)
        _logger.warning("VALIDAÇÃO STOCK.MOVE.LINE - Iniciando para %s linha(s)", len(self))
        _logger.warning("="*80)

        for line in self:
            _logger.warning("-"*80)
            _logger.warning("Validando Stock Move Line ID: %s", line.id)
            _logger.warning("  Produto: %s", line.product_id.name if line.product_id else "N/A")

            if not line.product_id:
                _logger.warning("  SKIP: Produto não definido")
                continue

            product_form = line.product_id.product_form if hasattr(line.product_id, 'product_form') else 'none'
            _logger.warning("  Forma do produto (product_form): %s", product_form)
            _logger.warning("  Dimensões atuais:")
            _logger.warning("    - Comprimento (length): %s", line.length)
            _logger.warning("    - Largura (width): %s", line.width)
            _logger.warning("    - Espessura (thickness): %s", line.thickness)
            _logger.warning("    - Unidades (units_qty): %s", line.units_qty)

            # Só valida se for um tipo que precisa de dimensões
            if product_form == 'none':
                _logger.warning("  SKIP: product_form = 'none', não requer dimensões")
                continue

            if product_form == 'block':
                _logger.warning("  Validando BLOCO: precisa length > 0 AND width > 0 AND thickness > 0")
                if not (line.length > 0 and line.width > 0 and line.thickness > 0):
                    _logger.error("  ❌ FALHOU: Bloco sem todas as dimensões preenchidas!")
                    _logger.error("    length > 0? %s (valor: %s)", line.length > 0, line.length)
                    _logger.error("    width > 0? %s (valor: %s)", line.width > 0, line.width)
                    _logger.error("    thickness > 0? %s (valor: %s)", line.thickness > 0, line.thickness)
                    raise ValidationError(
                        f"[PICKING/STOCK] Produto '{line.product_id.name}' do tipo 'Bloco' requer "
                        "Comprimento, Largura e Espessura preenchidos."
                    )
                else:
                    _logger.warning("  ✅ PASSOU: Bloco com todas as dimensões OK")

            elif product_form in ['slab', 'strip', 'tiles']:
                form_names = {'slab': 'Placa', 'strip': 'Banda', 'tiles': 'Ladrilhos'}
                form_name = form_names.get(product_form, product_form)
                _logger.warning("  Validando %s: precisa length > 0 AND width > 0", form_name.upper())

                if not (line.length > 0 and line.width > 0):
                    _logger.error("  ❌ FALHOU: %s sem comprimento e largura!", form_name)
                    _logger.error("    length > 0? %s (valor: %s)", line.length > 0, line.length)
                    _logger.error("    width > 0? %s (valor: %s)", line.width > 0, line.width)
                    raise ValidationError(
                        f"[PICKING/STOCK] Produto '{line.product_id.name}' do tipo '{form_name}' requer "
                        "Comprimento e Largura preenchidos."
                    )
                else:
                    _logger.warning("  ✅ PASSOU: %s com comprimento e largura OK", form_name)

        _logger.warning("="*80)
        _logger.warning("VALIDAÇÃO STOCK.MOVE.LINE - Concluída com SUCESSO")
        _logger.warning("="*80)

    @api.model_create_multi
    def create(self, vals_list):
        """Herda dimensões do move se não preenchidas"""
        for vals in vals_list:
            move_id = vals.get('move_id')
            if move_id:
                move = self.env['stock.move'].browse(move_id)
                if not vals.get('length') and move.length:
                    vals['length'] = move.length
                if not vals.get('width') and move.width:
                    vals['width'] = move.width
                if not vals.get('thickness') and move.thickness:
                    vals['thickness'] = move.thickness
                if not vals.get('units_qty') and move.units_qty:
                    vals['units_qty'] = move.units_qty
                if not vals.get('peso') and move.peso:
                    vals['peso'] = move.peso

        return super().create(vals_list)

    def _synchronize_quant(self, quantity, location, **kwargs):
        """Override para passar dimensões via contexto para criação de quants

        Este método é chamado por _action_done() quando o picking é validado.
        Passa as dimensões da move_line via contexto para que o stock.quant.create()
        possa capturá-las e preencher os campos length, width, thickness.
        """
        return super(StockMoveLine, self.with_context(
            move_line_length=self.length,
            move_line_width=self.width,
            move_line_thickness=self.thickness,
        ))._synchronize_quant(quantity, location, **kwargs)
