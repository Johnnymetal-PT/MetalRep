from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from odoo.tools.float_utils import float_round

class TransformationLineInput(models.Model):
    _name = 'transformation.line.input'
    _description = 'Linha de Entrada - Produtos para Transformar'
    _rec_name = 'product_id'

    _sql_constraints = [
        ('unique_quant_per_transformation',
         'unique(transformation_id, quant_id)',
         'Este quant já foi adicionado a este documento de transformação!')
    ]

    transformation_id = fields.Many2one(
        'transformation.document',
        string='Documento de Transformação',
        required=True,
        ondelete='cascade'
    )

    product_id = fields.Many2one(
        'product.product',
        string='Produto',
        required=True,
        domain="[('can_be_transformed', '=', True), ('product_form', 'in', ['block', 'slab'])]"
    )

    product_form = fields.Selection(
        related='product_id.product_form',
        string='Forma',
        readonly=True
    )

    lot_id = fields.Many2one(
        'stock.lot',
        string='Lote',
        domain="[('product_id', '=', product_id)]",
        help='Selecione o lote específico'
    )

    product_tracking = fields.Selection(
        related='product_id.tracking',
        string='Tracking',
        readonly=True
    )

    # Dimensões do produto (peça individual)
    length = fields.Float(
        string='Comprimento',
        digits='Dimensions',
        help='Comprimento específico da peça em metros'
    )

    width = fields.Float(
        string='Largura',
        digits='Dimensions',
        help='Largura específica da peça em metros'
    )

    thickness = fields.Float(
        string='Espessura',
        digits='Dimensions',
        help='Espessura específica da peça em metros'
    )

    units_qty = fields.Integer(
        string='Quantidade',
        default=1,
        help='Quantidade de unidades/peças a serem transformadas'
    )

    quantity = fields.Float(
        string='Volume/Área',
        required=True,
        digits='Product Unit of Measure'
    )

    product_uom_id = fields.Many2one(
        'uom.uom',
        string='Unidade',
        related='product_id.uom_id',
        readonly=True
    )

    quant_id = fields.Many2one(
        'stock.quant',
        string='Quant de Origem',
        help='Referência ao quant de onde veio este produto',
        readonly=True
    )

    preco_custo = fields.Float(
        string='Custo (PCMP do grupo)',
        compute='_compute_preco_custo',
        store=True,
        readonly=True,
        digits='Product Price',
        help='PCMP do base.lot.group (via price_group do lote). Live em rascunho; '
             'congela quando o documento sai de rascunho (action_start).'
    )

    subtotal = fields.Float(
        string='Subtotal',
        compute='_compute_subtotal',
        store=True
    )

    location_id = fields.Many2one(
        related='transformation_id.location_origin_id',
        string='Localização',
        readonly=True
    )

    # Campos de controle de ganho/perda
    volume_consumed = fields.Float(
        string='Volume Consumido',
        compute='_compute_volume_difference',
        store=True,
        digits='Product Unit of Measure',
        help='Volume total consumido pelos produtos de saída (outputs)'
    )

    volume_difference = fields.Float(
        string='Diferença',
        compute='_compute_volume_difference',
        store=True,
        digits='Product Unit of Measure',
        help='Diferença entre volume consumido e volume disponível (positivo = ganho, negativo = perda)'
    )

    volume_difference_percent = fields.Float(
        string='% Diferença',
        compute='_compute_volume_difference',
        store=True,
        digits=(10, 2),
        help='Percentual de ganho/perda em relação ao volume de entrada'
    )

    has_difference = fields.Boolean(
        string='Tem Diferença',
        compute='_compute_volume_difference',
        store=True,
        help='Indica se há ganho ou perda'
    )

    is_gain = fields.Boolean(
        string='É Ganho',
        compute='_compute_volume_difference',
        store=True,
        help='True se volume consumido > volume disponível'
    )

    is_loss = fields.Boolean(
        string='É Perda',
        compute='_compute_volume_difference',
        store=True,
        help='True se volume consumido < volume disponível'
    )

    admin_approved = fields.Boolean(
        string='Aprovado por Admin',
        default=False,
        readonly=True,
        help='Administrador aprovou o ganho ou perda',
        copy=False
    )

    @api.depends('transformation_id.output_line_ids',
                 'transformation_id.output_line_ids.quantity',
                 'transformation_id.output_line_ids.thickness',
                 'transformation_id.output_line_ids.input_line_id',
                 'quantity', 'product_form')
    def _compute_volume_difference(self):
        """Calcular diferença entre volume consumido e volume disponível"""
        for line in self:
            if not line.quantity or line.quantity <= 0:
                line.volume_consumed = 0.0
                line.volume_difference = 0.0
                line.volume_difference_percent = 0.0
                line.has_difference = False
                line.is_gain = False
                line.is_loss = False
                continue

            # Buscar todos os outputs relacionados a este input
            related_outputs = line.transformation_id.output_line_ids.filtered(
                lambda l: l.input_line_id == line
            )

            if not related_outputs:
                line.volume_consumed = 0.0
                line.volume_difference = 0.0
                line.volume_difference_percent = 0.0
                line.has_difference = False
                line.is_gain = False
                line.is_loss = False
                continue

            input_form = line.product_form

            # Calcular volume consumido
            if input_form == 'block':
                # Bloco → Placa: volume = Σ(área × espessura)
                total_volume_consumed = 0.0
                for output in related_outputs:
                    if output.thickness and output.thickness > 0:
                        volume_consumed = output.quantity * output.thickness
                        total_volume_consumed += volume_consumed

                line.volume_consumed = total_volume_consumed

            elif input_form in ['slab', 'strip']:
                # Placa → Banda ou Banda → Ladrilhos: área = Σ(área)
                total_area_consumed = sum(related_outputs.mapped('quantity'))
                line.volume_consumed = total_area_consumed

            else:
                line.volume_consumed = 0.0
                line.volume_difference = 0.0
                line.volume_difference_percent = 0.0
                line.has_difference = False
                line.is_gain = False
                line.is_loss = False
                continue

            # Calcular diferença
            line.volume_difference = line.volume_consumed - line.quantity

            # Calcular percentual
            if line.quantity > 0:
                line.volume_difference_percent = (line.volume_difference / line.quantity) * 100
            else:
                line.volume_difference_percent = 0.0

            # Definir flags
            tolerance = 0.0001  # Tolerância para arredondamento
            line.has_difference = abs(line.volume_difference) > tolerance
            line.is_gain = line.volume_difference > tolerance
            line.is_loss = line.volume_difference < -tolerance

    @api.depends('lot_id', 'lot_id.price_group_id.pcmp', 'transformation_id.state')
    def _compute_preco_custo(self):
        """Custo do input = PCMP do base.lot.group (via price_group do lote).

        Live enquanto o documento está em rascunho; CONGELA quando sai de
        rascunho (action_start = consumo), mantendo o valor já gravado.
        """
        for line in self:
            state = line.transformation_id.state if line.transformation_id else 'draft'
            if state == 'draft':
                line.preco_custo = line.lot_id.price_group_id.pcmp or 0.0
            else:
                # Congelado: mantém o snapshot do momento do action_start
                line.preco_custo = line.preco_custo

    @api.depends('quantity', 'preco_custo')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.preco_custo

    def action_approve_difference(self):
        """Aprovar a diferença (ganho/perda) desta(s) linha(s) individualmente.
        Permite aprovação selectiva, linha a linha, em vez de aprovar tudo de
        uma vez. Só admin. Regista no chatter do documento."""
        if not self.env.user.has_group('base.group_system'):
            raise UserError('Apenas administradores podem aprovar diferenças.')
        lines = self.filtered(lambda l: l.has_difference and not l.admin_approved)
        if not lines:
            raise UserError('Não há diferença pendente de aprovação nesta linha.')
        lines.write({'admin_approved': True})
        # Registar no chatter, agrupado por documento
        for doc in lines.mapped('transformation_id'):
            doc._post_approval_message(lines.filtered(lambda l: l.transformation_id == doc))
        return True

    def unlink(self):
        """Ao apagar uma linha de input, apagar também as linhas de output
        associadas a ela (input_line_id). Faz-se via unlink() do output para
        correr os hooks dele (sincronizar picking, redistribuir custos de
        serviço, repor aprovações)."""
        related_outputs = self.env['transformation.line.output'].search([
            ('input_line_id', 'in', self.ids)
        ])
        if related_outputs:
            related_outputs.unlink()
        return super().unlink()

    @api.constrains('quantity')
    def _check_quantity(self):
        for line in self:
            if line.quantity <= 0:
                raise ValidationError('O Volume/Área deve ser maior que zero.')

    @api.constrains('product_form')
    def _check_product_form(self):
        for line in self:
            if line.product_form == 'strip':
                raise ValidationError('Bandas não podem ser transformadas, são o produto final.')

    @api.constrains('product_id', 'lot_id')
    def _check_lot_required(self):
        """Verificar se o lote é obrigatório para produtos com tracking por lote"""
        for line in self:
            if line.product_id and line.product_id.tracking == 'lot' and not line.lot_id:
                raise ValidationError(
                    f'O produto "{line.product_id.display_name}" tem rastreamento por lote. '
                    f'É obrigatório selecionar um lote.'
                )

    @api.constrains('lot_id')
    def _check_lot_not_in_active_sale(self):
        """Impede transformar lote já vendido/reservado em ordem de venda ativa

        Valida que o lote selecionado não está sendo usado em uma ordem de venda
        confirmada ou finalizada antes de permitir a transformação.
        """
        for line in self:
            if line.lot_id:
                # Buscar linhas de venda com este lote em estados ativos
                sale_lines = self.env['sale.order.line'].search([
                    ('lot_id', '=', line.lot_id.id),
                    ('order_id.state', 'in', ['sale', 'done'])
                ])

                if sale_lines:
                    # Pegar primeira ordem encontrada para mensagem
                    sale_order = sale_lines[0].order_id

                    raise ValidationError(
                        f"❌ Lote {line.lot_id.name} já está vendido!\n\n"
                        f"Ordem de venda: {sale_order.name}\n"
                        f"Cliente: {sale_order.partner_id.name}\n"
                        f"Estado: {dict(sale_order._fields['state'].selection).get(sale_order.state)}\n\n"
                        f"💡 Lotes vendidos não podem ser transformados.\n"
                        f"Selecione um lote diferente."
                    )

    @api.constrains('lot_id', 'transformation_id')
    def _check_lot_not_in_other_transformation(self):
        """Impede usar lote em múltiplas transformações ativas simultaneamente

        Valida que o lote não está sendo usado em outra transformação
        que esteja em estado draft, transit, transforming ou reception.
        """
        for line in self:
            if line.lot_id and line.transformation_id:
                # Buscar outras linhas de input com mesmo lote em transformações ativas
                other_lines = self.search([
                    ('lot_id', '=', line.lot_id.id),
                    ('transformation_id.state', 'in', ['draft', 'transit', 'transforming', 'reception']),
                    ('id', '!=', line.id)  # Excluir a própria linha
                ])

                if other_lines:
                    # Pegar primeira transformação encontrada
                    other_transform = other_lines[0].transformation_id

                    raise ValidationError(
                        f"❌ Lote {line.lot_id.name} já está em outra transformação!\n\n"
                        f"Documento: {other_transform.name}\n"
                        f"Estado: {dict(other_transform._fields['state'].selection).get(other_transform.state)}\n\n"
                        f"💡 Finalize ou cancele a transformação existente antes de usar este lote novamente."
                    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Limpar lote ao trocar produto"""
        self.lot_id = False
        self.admin_approved = False
        if self.product_id:
            # Buscar lotes disponíveis
            location = self.location_id
            if location:
                domain = [
                    ('product_id', '=', self.product_id.id),
                    ('location_id', '=', location.id)
                ]
                quants = self.env['stock.quant'].search(domain)
                lot_ids = quants.mapped('lot_id').ids
                return {'domain': {'lot_id': [('id', 'in', lot_ids)]}}

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        """Atualizar dimensões e preço ao selecionar lote"""
        # Preencher dimensões do lote se aplicável
        if self.lot_id:
            product_form = self.product_id.product_form if self.product_id and hasattr(self.product_id, 'product_form') else 'none'

            if product_form in ['block', 'slab']:
                # Preencher dimensões do lote (se existirem)
                if hasattr(self.lot_id, 'length'):
                    self.length = self.lot_id.length or 0.0
                if hasattr(self.lot_id, 'width'):
                    self.width = self.lot_id.width or 0.0
                if hasattr(self.lot_id, 'thickness'):
                    self.thickness = self.lot_id.thickness or 0.0
                # preco_custo é computed (PCMP do grupo) — não se preenche aqui

    @api.onchange('length', 'width', 'thickness', 'units_qty')
    def _onchange_dimensions(self):
        """Recalcula a quantidade quando dimensões mudam"""
        product_form = self.product_id.product_form if self.product_id and hasattr(self.product_id, 'product_form') else 'none'

        if product_form in ['block', 'slab']:
            self._compute_quantity_from_dimensions()

    def _compute_quantity_from_dimensions(self):
        """Calcula quantity baseado nas dimensões e product_form"""
        if not self.product_id:
            return

        product_form = self.product_id.product_form if hasattr(self.product_id, 'product_form') else 'none'

        if product_form not in ['block', 'slab']:
            return

        units_qty = self.units_qty or 1  # Default 1 se vazio

        if product_form == 'block':
            # Volume total (m³) = comprimento × largura × espessura × unidades
            if self.length and self.width and self.thickness:
                calculated = self.length * self.width * self.thickness * units_qty
                # Arredondar com precision do UOM
                if self.product_uom_id:
                    self.quantity = float_round(calculated, precision_rounding=self.product_uom_id.rounding)
                else:
                    self.quantity = calculated
            else:
                self.quantity = 0.0

        elif product_form == 'slab':
            # Área total (m²) = comprimento × largura × unidades
            if self.length and self.width:
                calculated = self.length * self.width * units_qty
                # Arredondar com precision do UOM
                if self.product_uom_id:
                    self.quantity = float_round(calculated, precision_rounding=self.product_uom_id.rounding)
                else:
                    self.quantity = calculated
            else:
                self.quantity = 0.0

    @api.constrains('length', 'width', 'thickness', 'product_id')
    def _check_dimensions_required(self):
        """Valida que dimensões obrigatórias estão preenchidas"""
        for line in self:
            if not line.product_id:
                continue

            product_form = line.product_id.product_form if hasattr(line.product_id, 'product_form') else 'none'

            if product_form == 'none':
                continue

            if product_form == 'block':
                if not (line.length > 0 and line.width > 0 and line.thickness > 0):
                    raise ValidationError(
                        f'Produto "{line.product_id.display_name}" do tipo "Bloco" requer '
                        f'Comprimento, Largura e Espessura preenchidos.'
                    )

            elif product_form == 'slab':
                if not (line.length > 0 and line.width > 0):
                    raise ValidationError(
                        f'Produto "{line.product_id.display_name}" do tipo "Placa" requer '
                        f'Comprimento e Largura preenchidos.'
                    )

    def action_open_stock_wizard(self):
        """Abrir wizard de seleção de estoque disponível

        Método chamado do botão no <control> da lista de input_line_ids.
        Segue o padrão do Odoo (similar a sale.order.line).
        """
        transformation = self.env['transformation.document'].browse(
            self.env.context.get('transformation_id')
        )
        return transformation.action_open_stock_wizard()