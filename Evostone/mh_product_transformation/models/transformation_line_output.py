from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round

class TransformationLineOutput(models.Model):
    _name = 'transformation.line.output'
    _description = 'Linha de Saída - Produtos Finais'
    _rec_name = 'product_id'

    transformation_id = fields.Many2one(
        'transformation.document',
        string='Documento de Transformação',
        required=True,
        ondelete='cascade'
    )

    input_line_id = fields.Many2one(
        'transformation.line.input',
        string='Produto de Origem',
        required=True,
        domain="[('transformation_id', '=', transformation_id)]",
        help='Produto que será transformado neste produto final'
    )

    stock_move_id = fields.Many2one(
        'stock.move',
        string='Movimento de Stock',
        readonly=True,
        help='Movimento de entrada criado para este produto transformado'
    )

    input_product_form = fields.Selection(
        related='input_line_id.product_form',
        string='Forma de Origem',
        readonly=True
    )

    product_id = fields.Many2one(
        'product.product',
        string='Produto Final',
        required=True,
        domain="[('product_form', '=', expected_form)]"
    )

    expected_form = fields.Selection([
        ('none', 'Nenhum'),
        ('block', 'Bloco'),
        ('slab', 'Placa'),
        ('strip', 'Banda'),
        ('tiles', 'Ladrilhos')
    ], string='Forma Esperada',
       compute='_compute_expected_form',
       store=True,
       help='Forma esperada baseada no produto de origem'
    )

    # Dimensões do produto final
    length = fields.Float(
        string='Comprimento',
        digits='Dimensions',
        help='Comprimento da peça transformada em metros'
    )

    width = fields.Float(
        string='Largura',
        digits='Dimensions',
        help='Largura da peça transformada em metros'
    )

    thickness = fields.Float(
        string='Espessura',
        digits='Dimensions',
        help='Espessura da peça transformada em metros'
    )

    thickness_readonly = fields.Boolean(
        string='Thickness Readonly',
        compute='_compute_thickness_readonly',
        store=False,
        help='Controla se o campo thickness deve ser readonly'
    )

    units_qty = fields.Integer(
        string='Quantidade',
        default=1,
        help='Quantidade de unidades/peças transformadas'
    )

    quantity = fields.Float(
        string='Volume/Área',
        compute='_compute_quantity',
        store=True,
        readonly=True,
        digits='Product Unit of Measure',
        help='Calculado automaticamente baseado nas dimensões e unidades'
    )

    product_uom_id = fields.Many2one(
        'uom.uom',
        string='Unidade',
        related='product_id.uom_id',
        readonly=True
    )

    product_tracking = fields.Selection(
        related='product_id.tracking',
        string='Tracking',
        readonly=True
    )

    lot_name = fields.Char(
        string='Lote',
        help='Nome do lote das placas. Sugerido automaticamente a partir do '
             'base_lot_name do lote de entrada, mas editável pelo utilizador.'
    )

    price_unit = fields.Float(
        string='Preço Unitário',
        compute='_compute_price_unit',
        store=True,
        digits='Product Price',
        help='Preço unitário calculado baseado na distribuição proporcional do input'
    )

    landed_cost = fields.Float(
        string='Custo Adicional Total',
        digits='Product Price',
        help='Custo adicional TOTAL para esta linha (landed cost). Distribuído dos serviços de PO proporcionalmente.'
    )

    final_unit_cost = fields.Float(
        string='Custo Unitário Final',
        compute='_compute_final_unit_cost',
        store=True,
        digits='Product Price',
        help='Custo unitário final (preço unitário + custo adicional)'
    )

    pcmp_calculated = fields.Float(
        string='PCMP Calculado',
        digits='Product Price',
        help='PCMP calculado para este produto'
    )

    total_cost = fields.Float(
        string='Custo Total',
        compute='_compute_total_cost',
        store=True,
        digits='Product Price',
        help='Custo total desta linha de output (quantity × final_unit_cost)'
    )

    volume_consumed = fields.Float(
        string='Volume Consumido',
        compute='_compute_volume_consumed',
        store=True,
        digits='Product Unit of Measure',
        help='Volume/área consumido do produto de entrada (m³ para blocos, m² para placas/bandas)'
    )

    @api.depends('input_line_id', 'input_line_id.product_form', 'quantity', 'thickness')
    def _compute_volume_consumed(self):
        """Calcular volume/área consumido do produto de entrada"""
        for line in self:
            if not line.input_line_id or not line.quantity:
                line.volume_consumed = 0.0
                continue

            input_form = line.input_line_id.product_form

            if input_form == 'block':
                # Bloco → Placa: volume consumido = área × espessura
                if line.thickness and line.thickness > 0:
                    line.volume_consumed = line.quantity * line.thickness  # m³
                else:
                    line.volume_consumed = 0.0

            elif input_form in ['slab', 'strip']:
                # Placa → Banda ou Banda → Ladrilhos: área consumida = quantidade
                line.volume_consumed = line.quantity  # m²

            else:
                # Produto sem forma específica
                line.volume_consumed = line.quantity

    @api.depends('input_line_id', 'input_line_id.product_form')
    def _compute_expected_form(self):
        for line in self:
            if not line.input_line_id or not line.input_line_id.product_form:
                line.expected_form = False
            elif line.input_line_id.product_form == 'block':
                line.expected_form = 'slab'
            elif line.input_line_id.product_form == 'slab':
                line.expected_form = 'strip'
            elif line.input_line_id.product_form == 'strip':
                line.expected_form = 'tiles'
            else:
                line.expected_form = False

    @api.depends('product_id', 'product_id.product_form')
    def _compute_thickness_readonly(self):
        """Computar se o campo thickness deve ser readonly

        Readonly quando product_form for diferente de 'block' e 'none'
        Editável apenas quando product_form = 'block' ou 'none'
        """
        for line in self:
            if not line.product_id:
                line.thickness_readonly = False
                continue

            product_form = line.product_id.product_form if hasattr(line.product_id, 'product_form') else 'none'
            # Readonly para 'slab', 'strip', 'tiles' (auto-preenchidos)
            # Editável para 'block' e 'none'
            line.thickness_readonly = (product_form not in ['block', 'none'])

    @api.depends('length', 'width', 'thickness', 'units_qty', 'product_id')
    def _compute_quantity(self):
        """Calcular quantidade baseado nas dimensões e forma do produto"""
        for line in self:
            if not line.product_id:
                line.quantity = 0.0
                continue

            product_form = line.product_id.product_form if hasattr(line.product_id, 'product_form') else 'none'
            units_qty = line.units_qty or 1

            if product_form == 'block':
                # Volume (m³) = comprimento × largura × espessura × unidades
                if line.length and line.width and line.thickness:
                    calculated = line.length * line.width * line.thickness * units_qty
                    if line.product_uom_id:
                        line.quantity = float_round(calculated, precision_rounding=line.product_uom_id.rounding)
                    else:
                        line.quantity = calculated
                else:
                    line.quantity = 0.0

            elif product_form == 'slab':
                # Área (m²) = comprimento × largura × unidades
                if line.length and line.width:
                    calculated = line.length * line.width * units_qty
                    if line.product_uom_id:
                        line.quantity = float_round(calculated, precision_rounding=line.product_uom_id.rounding)
                    else:
                        line.quantity = calculated
                else:
                    line.quantity = 0.0

            elif product_form == 'strip':
                # Área (m²) = comprimento × largura × unidades
                # Bandas também usam área
                if line.length and line.width:
                    calculated = line.length * line.width * units_qty
                    if line.product_uom_id:
                        line.quantity = float_round(calculated, precision_rounding=line.product_uom_id.rounding)
                    else:
                        line.quantity = calculated
                else:
                    line.quantity = 0.0
            else:
                # Produtos sem forma específica
                line.quantity = units_qty

    @api.constrains('quantity')
    def _check_quantity(self):
        for line in self:
            if line.quantity <= 0:
                raise ValidationError('O Volume/Área deve ser maior que zero.')

    @api.constrains('quantity', 'thickness', 'input_line_id')
    def _check_output_quantity_vs_input(self):
        """Validar espessura obrigatória para placas (validação de ganho/perda movida para input line)"""
        for line in self:
            if not line.input_line_id or not line.quantity:
                continue

            input_form = line.input_line_id.product_form

            # Validar apenas que espessura está preenchida para placas (Bloco → Placa)
            if input_form == 'block':
                if not line.thickness or line.thickness <= 0:
                    raise ValidationError(
                        f'❌ Espessura da placa "{line.product_id.display_name}" não definida!\n\n'
                        f'É obrigatório informar a espessura da placa para calcular o volume consumido.'
                    )

    @api.constrains('product_id', 'lot_name', 'length', 'width', 'thickness', 'transformation_id')
    def _check_duplicate_output_line(self):
        """Evitar linhas de output duplicadas com mesmas características"""
        for line in self:
            if not line.product_id or not line.transformation_id:
                continue

            # Buscar outras linhas no mesmo documento com características idênticas
            duplicate = self.search([
                ('transformation_id', '=', line.transformation_id.id),
                ('product_id', '=', line.product_id.id),
                ('lot_name', '=', line.lot_name or False),
                ('length', '=', line.length or 0.0),
                ('width', '=', line.width or 0.0),
                ('thickness', '=', line.thickness or 0.0),
                ('id', '!=', line.id)  # Excluir a própria linha
            ], limit=1)

            if duplicate:
                raise ValidationError(
                    f'❌ Linha duplicada detectada!\n\n'
                    f'Já existe uma linha com as mesmas características:\n'
                    f'  • Produto: {line.product_id.display_name}\n'
                    f'  • Lote: {line.lot_name or "N/A"}\n'
                    f'  • Dimensões: {line.length or 0}m × {line.width or 0}m × {line.thickness or 0}m\n\n'
                    f'💡 Para adicionar mais quantidade, edite a linha existente\n'
                    f'   ou altere alguma característica (dimensões ou lote).'
                )

    @api.constrains('product_id', 'input_line_id')
    def _check_transformation_logic(self):
        """Validar lógica de transformação"""
        for line in self:
            if not line.input_line_id or not line.product_id:
                continue

            input_form = line.input_line_id.product_form
            output_form = line.product_id.product_form

            # Bloco só pode virar Placa
            if input_form == 'block' and output_form != 'slab':
                raise ValidationError('Bloco só pode ser transformado em Placa.')

            # Placa só pode virar Banda
            if input_form == 'slab' and output_form != 'strip':
                raise ValidationError('Placa só pode ser transformada em Banda.')

            # Banda não pode ser transformada
            if input_form == 'strip':
                raise ValidationError('Banda não pode ser transformada.')

    @api.constrains('lot_name', 'product_id')
    def _check_lot_name_required(self):
        """Validar que lot_name é obrigatório para produtos rastreados"""
        for line in self:
            if line.product_id and line.product_id.tracking in ('lot', 'serial'):
                if not line.lot_name:
                    raise ValidationError(
                        f'O produto "{line.product_id.display_name}" tem rastreamento por lote/serial. '
                        f'É obrigatório informar o nome do lote.'
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
        if product_form in ['slab', 'strip', 'tiles']:
            # Pegar thickness do produto se disponível
            if hasattr(self.product_id, 'thickness') and self.product_id.thickness:
                self.thickness = self.product_id.thickness

    @api.onchange('input_line_id')
    def _onchange_input_line_id(self):
        """Atualizar domínio do produto baseado na forma esperada E preencher lot_name"""
        self.product_id = False

        # Preencher lot_name automaticamente baseado no price_group_id.base_lot_name da linha de input
        if self.input_line_id and self.input_line_id.lot_id:
            # Buscar base_lot_name do price_group_id
            if hasattr(self.input_line_id.lot_id, 'price_group_id') and self.input_line_id.lot_id.sudo().price_group_id:
                if hasattr(self.input_line_id.lot_id.sudo().price_group_id, 'base_lot_name'):
                    self.lot_name = self.input_line_id.lot_id.sudo().price_group_id.base_lot_name
                else:
                    self.lot_name = False
            else:
                self.lot_name = False
        else:
            self.lot_name = False

        if self.input_line_id:
            # expected_form será computado automaticamente pelo @api.depends
            # Determinar a forma esperada baseada no input
            input_form = self.input_line_id.product_form
            expected = False

            if input_form == 'block':
                expected = 'slab'
            elif input_form == 'slab':
                expected = 'strip'
            elif input_form == 'strip':
                expected = 'tiles'

            # Retornar domínio baseado na forma esperada
            if expected:
                return {
                    'domain': {
                        'product_id': [('product_form', '=', expected)]
                    }
                }

    @api.depends('input_line_id', 'input_line_id.subtotal', 'input_line_id.quantity',
                 'input_line_id.product_form', 'quantity', 'thickness',
                 'transformation_id.output_line_ids', 'transformation_id.output_line_ids.quantity',
                 'transformation_id.output_line_ids.thickness', 'transformation_id.output_line_ids.input_line_id')
    def _compute_price_unit(self):
        """Calcular preço unitário baseado no volume/área consumido do input"""
        for line in self:
            if not line.input_line_id or not line.quantity:
                line.price_unit = 0.0
                continue

            # Custo total do input
            input_total_cost = line.input_line_id.subtotal
            input_quantity = line.input_line_id.quantity
            input_form = line.input_line_id.product_form

            if not input_quantity or input_quantity <= 0:
                line.price_unit = 0.0
                continue

            # Calcular volume/área consumido por este output
            if input_form == 'block':
                # Bloco → Placa: volume consumido = área × espessura
                if not line.thickness or line.thickness <= 0:
                    line.price_unit = 0.0
                    continue

                consumed = line.quantity * line.thickness  # volume em m³

            elif input_form in ['slab', 'strip']:
                # Placa → Banda ou Banda → Ladrilhos: área consumida = quantidade
                consumed = line.quantity  # área em m²

            else:
                # Produto sem forma específica: usar quantidade
                consumed = line.quantity

            # Calcular custo baseado no volume/área consumido
            # Custo por unidade de input (€/m³ ou €/m²)
            input_unit_cost = input_total_cost / input_quantity

            # Custo total desta linha baseado no que foi consumido
            line_total_cost = consumed * input_unit_cost

            # Preço unitário = custo total / quantidade de output
            if line.quantity > 0:
                line.price_unit = line_total_cost / line.quantity
            else:
                line.price_unit = 0.0

    @api.depends('price_unit', 'landed_cost', 'quantity')
    def _compute_final_unit_cost(self):
        """Calcular custo unitário final (preço unitário + custo adicional unitário)"""
        for line in self:
            # Obter precisão da moeda
            precision_digits = 2
            if line.transformation_id and line.transformation_id.currency_id:
                precision_digits = line.transformation_id.currency_id.decimal_places or 2

            # landed_cost é TOTAL, dividir por quantity para obter per-unit
            if line.quantity > 0:
                landed_cost_per_unit = float_round(
                    (line.landed_cost or 0.0) / line.quantity,
                    precision_digits=precision_digits
                )
                line.final_unit_cost = float_round(
                    (line.price_unit or 0.0) + landed_cost_per_unit,
                    precision_digits=precision_digits
                )
            else:
                line.final_unit_cost = line.price_unit or 0.0

    @api.depends('quantity', 'final_unit_cost')
    def _compute_total_cost(self):
        """Calcular custo total da linha"""
        for line in self:
            line.total_cost = line.quantity * line.final_unit_cost

    def write(self, vals):
        """Resetar admin_approved do input quando outputs mudarem e redistribuir custos"""
        result = super().write(vals)

        # Se mudou quantidade ou espessura, resetar aprovação do admin na linha de input
        if 'quantity' in vals or 'thickness' in vals or 'input_line_id' in vals:
            for line in self:
                if line.input_line_id and line.input_line_id.admin_approved:
                    line.input_line_id.admin_approved = False

        # Se mudou volume_consumed, redistribuir custos de serviço
        if 'quantity' in vals or 'thickness' in vals or 'length' in vals or 'width' in vals:
            for line in self:
                if line.transformation_id and line.transformation_id.state == 'draft':
                    if line.transformation_id.service_purchase_order_ids:
                        line.transformation_id._distribute_service_costs()

        # Sincronizar o picking de entrada (previsão de stock a chegar).
        # O próprio método só actua em transit/transforming/reception.
        sync_fields = {'quantity', 'length', 'width', 'thickness',
                       'units_qty', 'lot_name', 'product_id', 'product_uom_id'}
        if sync_fields & set(vals.keys()):
            for transformation in self.mapped('transformation_id'):
                transformation._sync_reception_picking()

        return result

    @api.model_create_multi
    def create(self, vals_list):
        """Resetar admin_approved do input ao criar novo output e redistribuir custos"""
        lines = super().create(vals_list)

        # Resetar aprovação do admin na linha de input
        for line in lines:
            if line.input_line_id and line.input_line_id.admin_approved:
                line.input_line_id.admin_approved = False

        # Redistribuir custos de serviço após criar novas linhas
        transformations = lines.mapped('transformation_id').filtered(
            lambda t: t.state != 'done'
        )
        for transformation in transformations:
            transformation._distribute_service_costs()

        # Sincronizar o picking de entrada (previsão de stock a chegar)
        for transformation in lines.mapped('transformation_id'):
            transformation._sync_reception_picking()

        return lines

    def unlink(self):
        """Resetar admin_approved do input ao deletar output e redistribuir custos"""
        # Guardar input_lines antes de deletar
        input_lines = self.mapped('input_line_id').filtered(lambda l: l.admin_approved)

        # Guardar transformations para redistribuir custos DEPOIS de deletar
        transformations = self.mapped('transformation_id').filtered(
            lambda t: t.state != 'done'
        )

        result = super().unlink()

        # Resetar aprovação
        for input_line in input_lines:
            input_line.admin_approved = False

        # Redistribuir custos de serviço após deletar linhas
        for transformation in transformations:
            transformation._distribute_service_costs()

        # Sincronizar o picking de entrada (remove moves das placas apagadas)
        for transformation in transformations:
            transformation._sync_reception_picking()

        return result