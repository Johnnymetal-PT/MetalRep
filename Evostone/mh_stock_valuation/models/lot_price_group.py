# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class LotPriceGroup(models.Model):
    _name = 'lot.price.group'
    _description = 'Grupo de Preços para Lotes com Dimensões Idênticas'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'product_id, name'

    name = fields.Char(
        string='Nome do Grupo',
        compute='_compute_name',
        store=True,
        readonly=True,
        help='Nome gerado automaticamente baseado em nome base do lote e dimensões'
    )
    
    description = fields.Char(
        string="Descrição",
        compute='_compute_name',
        store=True,
        readonly=True,
        help='Nome gerado automaticamente baseado no produto e dimensões'
    )

    base_lot_name = fields.Char(
        string='Nome Base do Lote',
        readonly=True,
        help='Nome base dos lotes deste grupo (ex: "LOTE_ABC")'
    )

    # Grupo base (hierarquia superior)
    base_lot_group_id = fields.Many2one(
        'base.lot.group',
        string='Grupo Base',
        compute='_compute_base_lot_group',
        store=True,
        readonly=True,
        help='Grupo base que agrupa por base_lot_name. Define preços padrão para este grupo de dimensões.'
    )

    use_base_pricing = fields.Boolean(
        string='Usar Preços do Grupo Base',
        default=True,
        help='Se marcado, herda preços do grupo base. Se desmarcado, permite definir margem e preço customizados.'
    )

    # Campos relacionados do grupo base para modo manual
    base_manual_sale_price = fields.Boolean(
        related='base_lot_group_id.manual_sale_price',
        string='Preço Manual (Base)',
        readonly=True,
        help='Indica se o grupo base usa preço de venda manual'
    )

    base_manual_pcmp = fields.Float(
        related='base_lot_group_id.manual_pcmp',
        string='PCMP Manual (Base)',
        readonly=True,
        help='PCMP manual do grupo base (usado quando manual_sale_price=True)'
    )

    product_id = fields.Many2one(
        'product.product',
        string='Produto',
        required=True,
        readonly=True,
        ondelete='cascade',
        help='Produto associado a este grupo'
    )

    currency_id = fields.Many2one(
        'res.currency',
        related='product_id.company_id.currency_id',
        string='Moeda',
        readonly=True,
    )

    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        default=lambda self: self.env.company,
        index=True,
        help='Empresa do grupo. Usado para resolver densidade default '
             'quando o produto é multi-company.',
    )

    product_form = fields.Selection(
        related='product_id.product_tmpl_id.product_form',
        string='Forma do Produto',
        store=True,
        readonly=True,
        help='Forma física do produto (Bloco, Placa, Banda, etc.)'
    )

    variant_description = fields.Char(
        related='product_id.variant_description',
        string='Atributos',
        store=True,
        readonly=True,
        help='Descrição dos atributos da variante do produto'
    )

    # Dimensões que definem o grupo
    length = fields.Float(
        string='Comprimento',
        digits='Dimensions',
        readonly=True,
        help='Comprimento em metros'
    )

    width = fields.Float(
        string='Largura',
        digits='Dimensions',
        readonly=True,
        help='Largura em metros'
    )

    thickness = fields.Float(
        string='Espessura',
        digits='Dimensions',
        readonly=True,
        help='Espessura em metros'
    )

    # Campos de área/volume calculados
    area = fields.Float(
        string='Área Unitária (m²)',
        compute='_compute_dimensions',
        store=True,
        readonly=True,
        digits='Product Unit of Measure',
        help='Área de uma unidade (comprimento × largura)'
    )

    volume = fields.Float(
        string='Volume Unitário (m³)',
        compute='_compute_dimensions',
        store=True,
        digits='Product Unit of Measure',
        help='Volume de uma unidade (comprimento × largura × espessura)'
    )

    # Peso unitário (kg por peça) — calculado a partir das dimensões
    peso = fields.Float(
        string='Peso Unitário (kg)',
        compute='_compute_peso',
        store=True,
        digits=(10, 2),
        help='Peso de uma peça em kg, calculado:\n'
             '- block: L × W × T × densidade\n'
             '- slab/strip/tiles: L × W × T × densidade\n'
             'Densidade: product.density ou parâmetro '
             'campo Empresa → Densidade Padrão de Pedra (default 2700 kg/m³).',
    )

    @api.depends('length', 'width', 'thickness', 'product_id',
                 'product_id.density', 'product_id.product_form',
                 'company_id.stone_density')
    def _compute_peso(self):
        for group in self:
            company_density = (group.company_id.stone_density
                               if group.company_id else 0) or 2700
            product_form = getattr(group.product_id, 'product_form', 'none')
            if product_form in ('block', 'slab', 'strip', 'tiles'):
                density = (group.product_id.density if group.product_id else 0) or company_density
                group.peso = (group.length or 0.0) * (group.width or 0.0) \
                             * (group.thickness or 0.0) * density
            else:
                group.peso = 0.0

    # Peso total (soma de todos os lotes)
    peso_total = fields.Float(
        string='Peso Total',
        compute='_compute_peso_total',
        store=True,
        digits=(10, 2),
        help='Soma do peso de todos os lotes em estoque (kg)'
    )

    # Valor manual do preço de venda (guardado quando use_base_pricing=False).
    # Campo plain stored (sem compute) para servir de fonte estável ao list_price,
    # evitando ciclos de recompute entre list_price e margin.
    manual_list_price = fields.Float(
        string='Preço Venda Manual',
        store=True,
        digits='Product Price',
        help='Valor manual do preço de venda quando use_base_pricing=False. '
             'Definido pelo utilizador via list_price ou margin.'
    )

    # Preços e margem do grupo
    list_price = fields.Float(
        string='Preço de Venda',
        compute='_compute_list_price_from_pcmp',
        inverse='_inverse_list_price',
        store=True,
        digits='Product Price',
        tracking=True,
        help='Preço de venda. Para use_base_pricing=True: pcmp × (1 + margin/100). '
             'Para use_base_pricing=False: lê de manual_list_price.'
    )

    # Campos RELATED do grupo base (sempre sincronizados automaticamente)
    standard_price = fields.Float(
        string='Custo',
        related='base_lot_group_id.standard_price',
        digits='Product Price',
        store=True,
        readonly=True,
        help='Custo unitário do grupo base (MT/m² ou MT/m³)'
    )

    pcmp = fields.Float(
        string='PCMP',
        related='base_lot_group_id.pcmp',
        digits='Product Price',
        store=True,
        readonly=True,
        help='PCMP do grupo base (MT/m² ou MT/m³)'
    )

    # Margem: related quando use_base_pricing=True, manual quando False
    margin = fields.Float(
        string='Margem (%)',
        compute='_compute_margin',
        inverse='_inverse_margin',
        store=True,
        tracking=True,
        help='Margem de lucro: herda do grupo base ou valor manual'
    )

    # Lotes associados
    lot_ids = fields.One2many(
        'stock.lot',
        'price_group_id',
        string='Lotes Associados',
        readonly=True,
    )

    lot_count = fields.Integer(
        string='Nº de Lotes',
        compute='_compute_lot_count',
        store=True,
        help='Quantidade de lotes associados a este grupo'
    )

    # Campos informativos
    total_quantity = fields.Float(
        string='Quantidade Total',
        digits='Product Unit of Measure',
        compute='_compute_totals',
        help='Soma das quantidades disponíveis de todos os lotes'
    )

    total_value = fields.Float(
        string='Valor Total',
        compute='_compute_totals',
        digits='Product Price',
        help='Valor total em estoque (quantidade × preço de venda)'
    )

    # Campos informativos - valores absolutos por peça (computed)
    cost_per_piece = fields.Float(
        string='Custo da Peça',
        compute='_compute_absolute_values',
        digits='Product Price',
        help='Custo absoluto da peça: standard_price (MT/m²) × área (m²)'
    )

    pcmp_per_piece = fields.Float(
        string='PCMP da Peça',
        compute='_compute_absolute_values',
        digits='Product Price',
        help='PCMP absoluto da peça: pcmp (MT/m²) × área (m²)'
    )

    list_price_per_piece = fields.Float(
        string='Preço Venda da Peça',
        compute='_compute_absolute_values',
        digits='Product Price',
        help='Preço de venda absoluto da peça: list_price (MT/m²) × área (m²)'
    )

    @api.depends('standard_price', 'pcmp', 'list_price', 'area', 'volume', 'product_form')
    def _compute_absolute_values(self):
        """Calcula valores absolutos por peça (informativos)

        Multiplica os valores unitários (por m²/m³) pela área ou volume
        conforme o product_form para obter o valor absoluto da peça.
        """
        for group in self:
            if group.product_form == 'block' and group.volume > 0:
                # Blocos: multiplicar por volume
                group.cost_per_piece = group.standard_price * group.volume
                group.pcmp_per_piece = group.pcmp * group.volume
                group.list_price_per_piece = group.list_price * group.volume
            elif group.product_form in ['slab', 'strip', 'tiles'] and group.area > 0:
                # Placas/Bandas/Tiles: multiplicar por área
                group.cost_per_piece = group.standard_price * group.area
                group.pcmp_per_piece = group.pcmp * group.area
                group.list_price_per_piece = group.list_price * group.area
            else:
                # Sem dimensões ou product_form = 'none'
                group.cost_per_piece = group.standard_price
                group.pcmp_per_piece = group.pcmp
                group.list_price_per_piece = group.list_price

    @api.depends('use_base_pricing', 'base_lot_group_id.margin', 'pcmp', 'manual_list_price')
    def _compute_margin(self):
        """Calcula margem:
        - use_base_pricing=True: herda do grupo base
        - use_base_pricing=False: margin = (manual_list_price - pcmp)/pcmp × 100.
          Recalcula quando pcmp ou manual_list_price mudam. NÃO depende de list_price
          (evita ciclo).
        """
        for group in self:
            if group.use_base_pricing and group.base_lot_group_id:
                group.margin = group.base_lot_group_id.margin
            elif (group.pcmp and group.pcmp > 0
                  and group.manual_list_price and group.manual_list_price > 0):
                group.margin = ((group.manual_list_price - group.pcmp) / group.pcmp) * 100
            else:
                # Sem dados - preservar valor stored
                if group.id:
                    self.env.cr.execute(
                        "SELECT margin FROM lot_price_group WHERE id = %s", (group.id,)
                    )
                    result = self.env.cr.fetchone()
                    group.margin = result[0] if result and result[0] else 0.0
                else:
                    group.margin = 0.0

    def _inverse_margin(self):
        """User edita margin manualmente (use_base_pricing=False):
        Recalcula manual_list_price = pcmp × (1 + margin/100).
        """
        for group in self:
            if group.use_base_pricing:
                continue
            if group.pcmp and group.pcmp > 0 and group.margin:
                group.manual_list_price = group.pcmp * (1 + group.margin / 100)

    @api.depends('base_lot_name', 'product_id')
    def _compute_base_lot_group(self):
        """Busca o grupo base correspondente ao base_lot_name + product_id + company_id"""
        for group in self:
            if group.base_lot_name and group.product_id:
                # Usar company do produto ou empresa actual
                company_id = group.product_id.company_id.id or self.env.company.id
                base_group = self.env['base.lot.group'].sudo().search([
                    ('base_lot_name', '=', group.base_lot_name),
                    ('product_id', '=', group.product_id.id),
                    ('company_id', '=', company_id),
                ], limit=1)
                group.base_lot_group_id = base_group.id if base_group else False
            else:
                group.base_lot_group_id = False

    @api.depends('base_lot_name', 'length', 'width', 'thickness')
    def _compute_name(self):
        """Gera nome descritivo baseado em nome base do lote e dimensões"""
        for group in self:
            # Usar base_lot_name ou fallback para 'SEM-NOME'
            base_name = group.base_lot_name or 'SEM-NOME'

            # Formatar dimensões
            if group.thickness and group.thickness > 0:
                # Blocos: mostrar 3 dimensões
                dims = f"{group.length:.3f}x{group.width:.3f}x{group.thickness:.3f}"
            elif group.width and group.width > 0:
                # Placas/Bandas: mostrar 2 dimensões
                dims = f"{group.length:.3f}x{group.width:.3f}"
            elif group.length and group.length > 0:
                # Apenas comprimento
                dims = f"{group.length:.3f}"
            else:
                dims = "SEM-DIM"
            group.description = f"{group.product_id.display_name}-{dims}"
            group.name = f"{base_name}-{dims}"

    @api.depends('length', 'width', 'thickness')
    def _compute_dimensions(self):
        """Calcula área e volume baseado nas dimensões"""
        for group in self:
            # Área (m²)
            if group.length and group.width:
                group.area = group.length * group.width
            else:
                group.area = 0.0

            # Volume (m³)
            if group.length and group.width and group.thickness:
                group.volume = group.length * group.width * group.thickness
            else:
                group.volume = 0.0

    @api.depends('pcmp', 'margin', 'use_base_pricing', 'manual_list_price',
                 'base_lot_group_id.list_price')
    def _compute_list_price_from_pcmp(self):
        """Calcula list_price (valor unitário por m²/m³):

        1. use_base_pricing=True:
           list_price = base_lot_group_id.list_price (copia do grupo base).

        2. use_base_pricing=False:
           list_price = manual_list_price (campo plain stored).
           manual_list_price é definido pelo inverse de list_price ou margin.
        """
        for group in self:
            if not group.use_base_pricing:
                # Lê do campo plain manual_list_price (sem ciclo de recompute)
                if group.manual_list_price and group.manual_list_price > 0:
                    group.list_price = group.manual_list_price
                elif group.pcmp > 0 and group.margin:
                    # Inicialização para registos novos
                    group.list_price = group.pcmp * (1 + group.margin / 100)
                elif group.pcmp > 0:
                    group.list_price = group.pcmp
                else:
                    group.list_price = 0.0
                continue

            # use_base_pricing=True: copiar directamente do grupo base
            group.list_price = group.base_lot_group_id.list_price if group.base_lot_group_id else 0.0

    def _inverse_list_price(self):
        """User edita list_price manualmente (use_base_pricing=False):
        - Copia o valor para manual_list_price (fonte plain stored, sem ciclo)
        - Recalcula margin = (list_price - pcmp)/pcmp × 100
        """
        for group in self:
            if group.use_base_pricing:
                continue
            if group.list_price and group.list_price > 0:
                group.manual_list_price = group.list_price
                if group.pcmp and group.pcmp > 0:
                    group.margin = ((group.list_price - group.pcmp) / group.pcmp) * 100

    @api.onchange('use_base_pricing')
    def _onchange_use_base_pricing(self):
        """Quando ativar 'Usar Preços Base', sincroniza margem do grupo base

        NOTA: standard_price e pcmp são campos related, sincronizam automaticamente.
        Apenas margin precisa ser copiado ao activar use_base_pricing.
        """
        if self.use_base_pricing and self.base_lot_group_id:
            # Copiar margem do grupo base (pcmp e standard_price são related)
            self.margin = self.base_lot_group_id.margin
            # NOTA: list_price é calculado automaticamente via _compute_list_price_from_pcmp

    @api.onchange('margin')
    def _onchange_margin(self):
        """User altera margin na UI (use_base_pricing=False):
        Atualiza list_price e manual_list_price em tempo real.
        """
        if not self.use_base_pricing and self.pcmp and self.pcmp > 0 and self.margin:
            new_price = self.pcmp * (1 + self.margin / 100)
            self.manual_list_price = new_price
            self.list_price = new_price

    @api.onchange('list_price')
    def _onchange_list_price(self):
        """User altera list_price na UI (use_base_pricing=False):
        Atualiza margin e manual_list_price em tempo real.
        """
        if not self.use_base_pricing and self.list_price and self.list_price > 0:
            self.manual_list_price = self.list_price
            if self.pcmp and self.pcmp > 0:
                self.margin = ((self.list_price - self.pcmp) / self.pcmp) * 100

    @api.depends('lot_ids')
    def _compute_lot_count(self):
        """Conta número de lotes associados"""
        for group in self:
            group.lot_count = len(group.lot_ids)

    @api.depends('lot_ids.quant_ids.available_quantity', 'lot_ids.quant_ids.location_id.usage', 'list_price')
    def _compute_totals(self):
        """Calcula quantidade total e valor total em estoque interno"""
        for group in self:
            total_qty = 0.0
            for lot in group.lot_ids:
                # Filtrar apenas quants em localizações internas (armazém)
                internal_quants = lot.quant_ids.filtered(
                    lambda q: q.location_id.usage == 'internal'
                )
                # Somar available_quantity apenas de localizações internas
                total_qty += sum(internal_quants.mapped('available_quantity'))

            group.total_quantity = total_qty
            group.total_value = total_qty * group.list_price

    @api.depends('lot_ids.peso', 'lot_ids.quant_ids.available_quantity', 'lot_ids.quant_ids.location_id.usage')
    def _compute_peso_total(self):
        """Soma o peso de cada lote em stock interno.

        Cada lote = 1 peça (placa/bloco/banda/ladrilho), por isso o total é
        a soma dos `lot.peso` dos lotes com qty > 0 em localização interna.
        """
        for group in self:
            total = 0.0
            for lot in group.lot_ids:
                in_stock = any(
                    q.location_id.usage == 'internal' and q.available_quantity > 0
                    for q in lot.quant_ids
                )
                if in_stock:
                    total += lot.peso or 0.0
            group.peso_total = total

    def write(self, vals):
        """Override write para sincronizar margem quando use_base_pricing muda

        NOTA: Todos os campos de preço (pcmp, standard_price, margin, list_price)
        sincronizam automaticamente para stock.lot via campos related.
        """
        # Verificar se está mudando use_base_pricing de False→True
        if 'use_base_pricing' in vals and vals['use_base_pricing']:
            for group in self:
                if not group.use_base_pricing and group.base_lot_group_id:
                    # Copiar margem do grupo base
                    vals['margin'] = group.base_lot_group_id.margin

        return super().write(vals)

    @api.model
    def find_or_create_group(self, product_id, length, width, thickness, final_cost, pcmp, base_lot_name, company_id=None):
        """
        Busca grupo existente ou cria novo para dimensões e nome base específicos

        Args:
            product_id: ID do produto
            length: Comprimento
            width: Largura
            thickness: Espessura
            final_cost: Custo unitário (por m²/m³)
            pcmp: PCMP unitário (por m²/m³)
            base_lot_name: Nome base do lote (opcional)
            company_id: ID da empresa (opcional, usa empresa actual se não especificado)

        Returns:
            Recordset do lot.price.group

        NOTA: Todos os valores são unitários (por m²/m³).
        A multiplicação por área acontece apenas na sale.order.line.
        """
        # Normalizar valores None para 0.0 para comparação
        length = length or 0.0
        width = width or 0.0
        thickness = thickness or 0.0
        base_lot_name = base_lot_name or ''

        # Usar empresa actual se não especificada
        if company_id is None:
            company_id = self.env.company.id

        # Buscar grupo existente
        domain = [
            ('product_id', '=', product_id),
            ('length', '=', length),
            ('width', '=', width),
            ('thickness', '=', thickness),
            ('base_lot_name', '=', base_lot_name),
        ]

        group = self.search(domain, limit=1)

        if group:
            return group

        # Buscar ou criar grupo base (hierarquia superior)
        base_lot_group = None
        if base_lot_name:
            # Buscar grupo base existente (com company_id)
            base_lot_group = self.env['base.lot.group'].sudo().search([
                ('product_id', '=', product_id),
                ('base_lot_name', '=', base_lot_name),
                ('company_id', '=', company_id),
            ], limit=1)

            # Se não existir, criar novo (sudo para garantir permissões)
            # NOTA: standard_price e pcmp são campos COMPUTED - não passar valores!
            # O pcmp é calculado automaticamente das SVLs via _compute_pcmp()
            # O standard_price é calculado automaticamente via _compute_svl_values()
            if not base_lot_group:
                base_lot_group = self.env['base.lot.group'].sudo().create({
                    'product_id': product_id,
                    'base_lot_name': base_lot_name,
                    'company_id': company_id,
                    # NÃO passar standard_price nem pcmp - são computed!
                })

        # Criar lot.price.group (standard_price/pcmp são related, peso é computed)
        if base_lot_group:
            group = self.sudo().create({
                'product_id': product_id,
                'length': length,
                'width': width,
                'thickness': thickness,
                'base_lot_name': base_lot_name,
                # standard_price e pcmp são related fields, vêm do base_lot_group
                # margin é computed quando use_base_pricing=True
                # peso é computed a partir de length × width × thickness × density
                'use_base_pricing': True,
            })
        else:
            # Se não há base_lot_name, criar sem grupo base
            group = self.sudo().create({
                'product_id': product_id,
                'length': length,
                'width': width,
                'thickness': thickness,
                'base_lot_name': base_lot_name,
                # Sem grupo base, standard_price e pcmp serão 0 (related fields)
                # peso é computed
                'use_base_pricing': False,
            })

        return group

    def action_view_lots(self):
        """Ação para abrir lista de lotes associados"""
        self.ensure_one()
        return {
            'name': f'Lotes - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.lot',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.lot_ids.ids)],
            'context': {'default_price_group_id': self.id}
        }
