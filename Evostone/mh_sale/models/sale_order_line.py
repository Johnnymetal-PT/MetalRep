from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round
import logging

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    lot_id = fields.Many2one(
        "stock.lot",
        "SN",
        copy=False,
        help="Select a lot/serial number for this product"
    )

    lot_required = fields.Boolean(
        string="Lot Required",
        compute="_compute_lot_required",
        store=False,
    )

    # Dimensões do produto vendido (peça individual)
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
        help='Quantidade de unidades/peças a serem vendidas'
    )

    area = fields.Float(
        string='Área (m²)',
        compute='_compute_area_volume',
        store=True,
        digits='Product Unit of Measure',
        help='Área total da linha: comprimento × largura × quantidade de unidades.'
    )

    volume = fields.Float(
        string='Volume (m³)',
        compute='_compute_area_volume',
        store=True,
        digits='Product Unit of Measure',
        help='Volume total da linha: comprimento × largura × espessura × quantidade de unidades.'
    )

    peso = fields.Float(
        string='Peso',
        digits=(16, 2),
        compute='_compute_peso',
        store=True,
        readonly=False,
        help='Peso da linha em kg. Quando state in (sale,done), valor é '
             'congelado (snapshot histórico). Caso contrário, cascata: '
             'lot.peso → product_uom_qty × (thickness ×) density → product.weight × qty.',
    )

    @api.depends('state', 'thickness', 'product_uom_qty', 'product_id',
                 'product_id.density', 'product_id.weight', 'product_id.product_form',
                 'lot_id', 'lot_id.peso',
                 'company_id.stone_density')
    def _compute_peso(self):
        """Peso por product_form usando product_uom_qty (mesma fórmula do
        stock.move) com cascata para lot.peso. Quando state in ('sale','done')
        E peso já tem valor, preserva (snapshot histórico)."""
        for line in self:
            if line.state in ('sale', 'done') and line.peso:
                continue
            default_density = (line.company_id.stone_density
                               if line.company_id else 0) or 2700
            product_form = getattr(line.product_id, 'product_form', 'none')
            qty = line.product_uom_qty or 0.0
            if product_form in ('block', 'slab', 'strip', 'tiles'):
                # Prioridade lot.peso (peso real medido do slab vendido)
                if line.lot_id and line.lot_id.peso:
                    line.peso = line.lot_id.peso
                else:
                    density = (line.product_id.density if line.product_id else 0) or default_density
                    if product_form == 'block':
                        line.peso = qty * density
                    else:
                        line.peso = qty * (line.thickness or 0.0) * density
            else:
                line.peso = qty * (line.product_id.weight or 0.0)

    lot_editable = fields.Boolean(
        string='Lote Editável',
        compute='_compute_lot_editable',
        store=False,
        help='Indica se lot_base_name pode ser editado (apenas se product_form != none)'
    )

    can_edit_price = fields.Boolean(
        string='Pode Editar Preço',
        compute='_compute_can_edit_price',
        store=False,
        help='Indica se o utilizador pode editar o preço unitário'
    )
    
    thickness_editable = fields.Boolean(
        string='Espessura Editável',
        compute='_compute_lot_editable',
        store=False,
        help='Indica se thickness_editable pode ser editado (apenas se product_form == block)'
    )
    
    units_qty_editable = fields.Boolean(
        string='Quantidade Editável',
        compute='_compute_lot_editable',
        store=False,
        help='Indica se units_qty pode ser editado (apenas se product_form == none)'
    )

    dimensions_editable = fields.Boolean(
        string='Dimensões Editáveis',
        compute='_compute_lot_editable',
        store=False,
        help='Cotação manual: permite editar length/width/thickness sem lote '
             '(state draft/sent e produto dimensional sem lot_id).'
    )

    # Campos de margem de lucro
    purchase_price = fields.Float(
        string='Cost',
        compute='_compute_purchase_price',
        store=True,
        digits='Product Price',
        groups='base.group_user',
        help='Custo unitário do produto (hierarquia: PCMP > standard_price)'
    )

    cost_at_confirmation = fields.Float(
        string='Custo na Confirmação',
        digits='Product Price',
        copy=False,
        readonly=True,
        help='Custo unitário congelado no momento da confirmação da venda'
    )

    weight_at_confirmation = fields.Float(
        string='Peso na Confirmação',
        digits=(10, 2),
        copy=False,
        readonly=True,
        help='Peso congelado no momento da confirmação da venda (kg)'
    )

    margin_amount = fields.Monetary(
        string='Valor da Margem',
        compute='_compute_margin',
        store=True,
        currency_field='currency_id',
        help='Valor da margem de lucro: (preço - custo) × quantidade'
    )

    margin_percent = fields.Float(
        string='Margem (%)',
        compute='_compute_margin',
        store=True,
        digits='Product Price',
        help='Mesma margem que margin, para compatibilidade com views'
    )

    # ========================================
    # CAMPOS DE HISTÓRICO (Antes do Ajuste CMV)
    # ========================================
    purchase_price_hist = fields.Float(
        string='Custo Histórico',
        digits='Product Price',
        copy=False,
        readonly=True,
        help='Custo unitário original antes do ajuste (período provisório)'
    )

    margin_amount_hist = fields.Monetary(
        string='Margem Histórica',
        currency_field='currency_id',
        copy=False,
        readonly=True,
        help='Margem original antes do ajuste de custo'
    )

    margin_percent_hist = fields.Float(
        string='Margem Histórica (%)',
        digits='Product Price',
        copy=False,
        readonly=True,
        help='Margem % original antes do ajuste de custo'
    )

    import_document_ids = fields.Many2many(
        'import.document',
        'sale_line_import_document_rel',
        'sale_line_id',
        'import_document_id',
        string='Documentos de Importação',
        copy=False,
        readonly=True,
        help='Documentos de importação que ajustaram o custo desta linha'
    )

    has_cost_adjustment = fields.Boolean(
        string='Tem Ajuste',
        compute='_compute_has_cost_adjustment',
        store=True,
        help='Indica se esta linha teve ajuste de custo'
    )

    @api.depends('import_document_ids')
    def _compute_has_cost_adjustment(self):
        """Verifica se a linha tem ajuste de custo (via importação)"""
        for line in self:
            line.has_cost_adjustment = bool(line.import_document_ids)

    @api.depends('lot_id', 'lot_id.pcmp',
                 'lot_id.price_group_id', 'lot_id.price_group_id.pcmp',
                 'product_id', 'product_id.pcmp', 'product_id.product_form',
                 'order_id.state', 'cost_at_confirmation')
    def _compute_purchase_price(self):
        """Calcula custo unitário baseado APENAS em PCMP (sem fallback para standard_price).

        IMPORTANTE: Se a venda já está confirmada (state='sale'/'done') e tem
        cost_at_confirmation, usa o valor congelado para manter histórico correcto.

        REGRA: Se PCMP = 0, purchase_price = 0 → margin = 0
        Quando PCMP for atualizado, a margem recalcula automaticamente.

        Para product_form='none' (produto simples):
            1. product.pcmp (se > 0)
            2. Se PCMP = 0 → purchase_price = 0 → margin = 0

        Para product_form!='none' (produto dimensional com lote):
            1. lot.pcmp (se > 0)
            2. lot.price_group_id.pcmp (se > 0)
            3. Se PCMP = 0 → purchase_price = 0 → margin = 0
        """
        for line in self:
            # Se já confirmado e tem custo congelado, usar esse valor
            if line.order_id.state in ['sale', 'done'] and line.cost_at_confirmation > 0:
                line.purchase_price = line.cost_at_confirmation
                continue

            product_form = line.product_id.product_form if line.product_id and hasattr(line.product_id, 'product_form') else 'none'
            cost = 0.0

            if product_form == 'none':
                # Produto simples: usa apenas PCMP (sem fallback para standard_price)
                if line.product_id:
                    if hasattr(line.product_id, 'pcmp') and line.product_id.pcmp > 0:
                        cost = line.product_id.pcmp
                    # Se PCMP = 0, cost fica 0 → margin = 0
            else:
                # Produto dimensional: hierarquia lot.pcmp → price_group.pcmp (sem fallbacks standard_price)
                if line.lot_id:
                    # 1. lot.pcmp
                    if hasattr(line.lot_id, 'pcmp') and line.lot_id.pcmp > 0:
                        cost = line.lot_id.pcmp
                    # 2. lot.price_group_id.pcmp
                    elif hasattr(line.lot_id, 'price_group_id') and line.lot_id.sudo().price_group_id:
                        if line.lot_id.sudo().price_group_id.pcmp > 0:
                            cost = line.lot_id.sudo().price_group_id.pcmp
                    # Se PCMP = 0, cost fica 0 → margin = 0

            line.purchase_price = cost

    @api.depends('price_subtotal', 'product_uom_qty', 'purchase_price')
    def _compute_margin(self):
        """Calcula margem de lucro baseado no price_subtotal (receita com descontos)

        Fórmulas (Markup - sobre custo):
            cost_total = purchase_price × product_uom_qty
            margin_amount = price_subtotal - cost_total
            margin_percent = (price_subtotal - cost_total) / cost_total

        Exemplo:
            Custo unitário: 100 MT, Quantidade: 2, Preço: 130 MT, Desconto: 10%
            price_subtotal = 130 × 2 × 0.9 = 234 MT
            cost_total = 100 × 2 = 200 MT
            margin_amount = 234 - 200 = 34 MT
            margin_percent = 34 / 200 = 0.17 (17%)
        """
        for line in self:
            # Custo total da linha
            cost_total = line.purchase_price * line.product_uom_qty

            # Calcular margem sobre receita real (com descontos)
            if cost_total > 0 and line.price_subtotal > 0:
                # Margem em valor = receita líquida - custo total
                line.margin_amount = line.price_subtotal - cost_total
                # Margem % (Markup) = lucro / custo (decimal para widget percentage)
                line.margin_percent = (line.price_subtotal - cost_total) / cost_total
            else:
                line.margin_amount = 0.0
                line.margin_percent = 0.0

    def _prepare_procurement_values(self, group_id=False):
        vals = super()._prepare_procurement_values(group_id=group_id)
        if self.lot_id:
            vals["restrict_lot_id"] = self.lot_id.id
        
        # Passar dimensões para o stock.move
        product_form = self.product_id.product_form if self.product_id and hasattr(self.product_id, 'product_form') else 'none'
        if product_form in ['block', 'slab', 'strip', 'tiles']:
            vals.update({
                'length': self.length,
                'width': self.width,
                'thickness': self.thickness,
                'units_qty': self.units_qty,
            })
        else:
            vals.update({
                'units_qty': self.units_qty,
            })
            _logger.warning("  Dimensões adicionadas ao move_vals: %s", vals)
        return vals

    @api.depends('product_uom_qty', 'product_id.product_form')
    def _compute_area_volume(self):
        """Área e volume da linha = product_uom_qty (UoM do produto).

        - product_form == 'block': UoM é m³ → volume = product_uom_qty
        - product_form in ('slab', 'strip', 'tiles'): UoM é m² → área = product_uom_qty
        - product_form == 'none' ou sem product_form: ambos a 0
        """
        for line in self:
            product_form = line.product_id.product_form if line.product_id and hasattr(line.product_id, 'product_form') else 'none'
            qty = line.product_uom_qty or 0.0
            if product_form == 'block':
                line.area = 0.0
                line.volume = qty
            elif product_form in ('slab', 'strip', 'tiles'):
                line.area = qty
                line.volume = 0.0
            else:
                line.area = 0.0
                line.volume = 0.0

    @api.depends("product_id", "product_id.tracking", "order_id.state")
    def _compute_lot_required(self):
        """Compute if lot is required based on product tracking and product form.

        Em draft/sent o lote NÃO é obrigatório (suporta cotação manual com
        dimensões livres). Mal a SO seja confirmada, lot_required passa a True
        e o save bloqueia sem lote.
        """
        for line in self:
            product_form = line.product_id.product_form if line.product_id and hasattr(line.product_id, 'product_form') else 'none'
            is_dimensional = (
                line.product_id
                and line.product_id.tracking in ['lot', 'serial']
                and line.product_id.type == 'consu'
                and product_form in ['block', 'slab', 'strip', 'tiles']
            )
            state = line.order_id.state if line.order_id else 'draft'
            line.lot_required = bool(is_dimensional) and state not in ('draft', 'sent')

    @api.constrains('product_id', 'lot_id', 'product_uom_qty')
    def _check_lot_required(self):
        """Check if lot is provided when required"""
        for line in self:
            # Fluxo Stone Trading (MZ): nas empresas em standard nao se aplica.
            if line.order_id and not line.order_id._mh_stone_gates_apply():
                continue

            # Só validar quando ordem está confirmada ou finalizada
            if line.order_id.state == 'draft':
                continue
            
            product_form = line.product_id.product_form if line.product_id and hasattr(line.product_id, 'product_form') else 'none'
            if (line.product_id
                and line.product_id.tracking in ['lot', 'serial']
                and line.product_id.type == 'consu'
                and product_form in ['block', 'slab', 'strip', 'tiles']
                and not line.lot_id):
                raise ValidationError(
                    _("O produto '%s' requer um lote/número de série para venda.")
                    % line.product_id.display_name
                )

    @api.constrains('lot_id', 'product_id', 'product_uom_qty', 'state', 'order_id')
    def _check_stock_availability(self):
        """Valida disponibilidade de stock baseado em stock.quant

        Verifica se o produto/lote tem quantidade disponível em stock.
        Considera automaticamente devoluções e notas de crédito pois
        o Odoo actualiza stock.quant quando há movimentação de retorno.
        """
        for line in self:
            # Fluxo Stone Trading (MZ): nas empresas em standard nao se aplica.
            if line.order_id and not line.order_id._mh_stone_gates_apply():
                continue

            # Só validar quando ordem está confirmada ou finalizada
            if line.order_id.state not in ['sale', 'done']:
                continue

            # Ignorar linhas de seção/nota
            if line.display_type:
                continue

            # Ignorar produtos sem stock (serviços, etc.)
            if not line.product_id or line.product_id.type != 'product':
                continue

            # Construir domínio base
            domain = [
                ('product_id', '=', line.product_id.id),
                ('location_id.usage', '=', 'internal'),
            ]

            # Se tem lote, filtrar por lote
            if line.lot_id:
                domain.append(('lot_id', '=', line.lot_id.id))

            # Verificar disponibilidade real em stock
            quants = self.env['stock.quant'].search(domain)
            available_qty = sum(quants.mapped('available_quantity'))

            if available_qty <= 0:
                if line.lot_id:
                    raise ValidationError(
                        f"❌ Lote {line.lot_id.name} não tem quantidade disponível!\n\n"
                        f"Produto: {line.product_id.display_name}\n"
                        f"Quantidade em Stock: {available_qty}\n\n"
                        f"💡 Verifique o histórico de movimentação do lote."
                    )
                else:
                    raise ValidationError(
                        f"❌ Produto {line.product_id.display_name} não tem quantidade disponível!\n\n"
                        f"Quantidade em Stock: {available_qty}\n\n"
                        f"💡 Verifique o stock do produto."
                    )

    @api.constrains('length', 'width', 'thickness', 'product_id', 'product_uom_qty', 'display_type')
    def _check_dimensions_required(self):
        """Valida que dimensões obrigatórias estão preenchidas para produtos específicos.

        Nota: Só valida quando estado != 'draft' para evitar erros durante edição.
        """
        for line in self:
            # Fluxo Stone Trading (MZ): nas empresas em standard nao se aplica.
            if line.order_id and not line.order_id._mh_stone_gates_apply():
                continue

            if line.order_id.state == 'draft':
                continue

            # Ignorar linhas de seção e nota
            if line.display_type:
                continue

            if not line.product_id or line.product_uom_qty <= 0:
                continue

            product_form = line.product_id.product_form if hasattr(line.product_id, 'product_form') else 'none'

            # Só valida se for um tipo que precisa de dimensões
            if product_form == 'none':
                _logger.warning("  SKIP: product_form = 'none', não requer dimensões")
                continue

            if product_form == 'block':
                if not (line.length > 0 and line.width > 0 and line.thickness > 0):
                    raise ValidationError(
                        _("[VENDA] Produto '%s' do tipo 'Bloco' requer Comprimento, Largura e Espessura preenchidos.")
                        % line.product_id.display_name
                    )

            elif product_form in ['slab', 'strip', 'tiles']:
                form_names = {'slab': 'Placa', 'strip': 'Banda', 'tiles': 'Ladrilhos'}
                form_name = form_names.get(product_form, product_form)

                if not (line.length > 0 and line.width > 0):
                    raise ValidationError(
                        _("[VENDA] Produto '%s' do tipo '%s' requer Comprimento e Largura preenchidos.")
                        % (line.product_id.display_name, form_name)
                    )


    @api.constrains('price_unit', 'product_id', 'display_type')
    def _check_price_unit_positive(self):
        """Validar que price_unit é maior que zero para linhas de produto"""
        for line in self:
            # Fluxo Stone Trading (MZ): nas empresas em standard nao se aplica.
            if line.order_id and not line.order_id._mh_stone_gates_apply():
                continue

            # Ignorar validação em rascunho - será validado ao confirmar
            if line.order_id.state == 'draft':
                continue
            
            # Ignorar linhas de seção/nota
            if line.display_type:
                continue

            # Só validar linhas com produto
            if not line.product_id:
                continue

            # Validar que price_unit > 0
            if line.price_unit <= 0:
                raise ValidationError(
                    _('❌ Preço unitário inválido!\n\n'
                      'Produto: %(product)s\n'
                      'Preço unitário: %(price).2f\n\n'
                      '💡 O preço unitário deve ser maior que zero.'
                    ) % {
                        'product': line.product_id.display_name,
                        'price': line.price_unit,
                    }
                )
    
    @api.constrains('product_uom_qty', 'product_id', 'display_type')
    def _check_quantity_positive(self):
        """Validar que product_uom_qty é maior que zero para linhas de produto.

        Nota: Só valida quando estado != 'draft' para evitar erros durante edição.
        """
        for line in self:
            # Fluxo Stone Trading (MZ): nas empresas em standard nao se aplica.
            if line.order_id and not line.order_id._mh_stone_gates_apply():
                continue

            # Ignorar validação em rascunho - será validado ao confirmar
            if line.order_id.state == 'draft':
                continue

            # Ignorar linhas de seção/nota
            if line.display_type:
                continue

            # Só validar linhas com produto
            if not line.product_id:
                continue

            # Validar que product_uom_qty > 0
            if line.product_uom_qty <= 0:
                raise ValidationError(
                    _('❌ Quantidade inválida!\n\n'
                      'Produto: %(product)s\n'
                      'Quantidade: %(qty).2f\n\n'
                      '💡 A quantidade deve ser maior que zero.'
                    ) % {
                        'product': line.product_id.display_name,
                        'qty': line.product_uom_qty,
                    }
                )

    @api.constrains('discount')
    def _check_discount_limit(self):
        """Validar limite de desconto baseado em permissões e configuração"""
        # Obter limite configurado (padrão 5%)
        discount_limit = float(self.env['ir.config_parameter'].sudo().get_param(
            'mh_sale.sale_discount_limit', default=5.0
        ))

        for line in self:
            # Fluxo Stone Trading (MZ): nas empresas em standard nao se aplica.
            if line.order_id and not line.order_id._mh_stone_gates_apply():
                continue

            # Ignorar validação em rascunho - será validado ao confirmar
            if line.order_id.state == 'draft':
                continue
            
            # Pular se desconto está desativado ou não há desconto/produto
            if not line.order_id.env.user.has_group('sale.group_discount_per_so_line'):
                continue
            if not line.discount or not line.product_id:
                continue

            # Verificar se usuário é admin ou gerente
            is_admin = line.env.user.has_group('base.group_system') or \
                       line.env.user.has_group('sales_team.group_sale_manager')

            # Se não for admin, validar limite configurado
            if not is_admin and line.discount > discount_limit:
                raise ValidationError(
                    _('❌ Desconto não permitido!\n\n'
                      'Produto: %(product)s\n'
                      'Desconto aplicado: %(discount).2f%%\n'
                      'Desconto máximo permitido: %(limit).2f%%\n\n'
                      '💡 Ação necessária:\n'
                      '   - Reduza o desconto para %(limit).2f%% ou menos\n'
                      '   OU\n'
                      '   - Solicite aprovação de um administrador/gerente de vendas'
                    ) % {
                        'product': line.product_id.display_name,
                        'discount': line.discount,
                        'limit': discount_limit
                    }
                )
                
    # ========================================
    # MÉTODOS DE VALIDAÇÃO (chamados ao confirmar)
    # ========================================

    def _validate_lot_required(self):
        """Validação de lote (chamada ao confirmar pedido).

        Em cotação manual (draft/sent) o lote é opcional para permitir entrar
        dimensões livremente. Ao confirmar a SO, produtos dimensionais com
        tracking obrigam selecção de lote.
        """
        for line in self:
            if line.display_type:
                continue
            if not line.product_id:
                continue
            product_form = line.product_id.product_form if hasattr(line.product_id, 'product_form') else 'none'
            if (line.product_id.tracking in ['lot', 'serial']
                    and line.product_id.type == 'consu'
                    and product_form in ['block', 'slab', 'strip', 'tiles']
                    and not line.lot_id):
                raise ValidationError(
                    _("[VENDA] Produto '%s' requer selecção de lote antes de confirmar a ordem. "
                      "Use o botão 'Selecionar Stock'.")
                    % line.product_id.display_name
                )

    def _validate_dimensions(self):
        """Validação de dimensões (chamada ao confirmar pedido)"""
        for line in self:
            if line.display_type:
                continue
            if not line.product_id or line.product_uom_qty <= 0:
                continue

            product_form = line.product_id.product_form if hasattr(line.product_id, 'product_form') else 'none'

            if product_form == 'none':
                continue

            if product_form == 'block':
                if not (line.length > 0 and line.width > 0 and line.thickness > 0):
                    raise ValidationError(
                        _("[VENDA] Produto '%s' do tipo 'Bloco' requer Comprimento, Largura e Espessura preenchidos.")
                        % line.product_id.display_name
                    )

            elif product_form in ['slab', 'strip', 'tiles']:
                form_names = {'slab': 'Placa', 'strip': 'Banda', 'tiles': 'Ladrilhos'}
                form_name = form_names.get(product_form, product_form)

                if not (line.length > 0 and line.width > 0):
                    raise ValidationError(
                        _("[VENDA] Produto '%s' do tipo '%s' requer Comprimento e Largura preenchidos.")
                        % (line.product_id.display_name, form_name)
                    )
                    

    def _validate_price_unit_positive(self):
        """Validação de preço unitário (chamada ao confirmar pedido)"""
        for line in self:
            if line.display_type:
                continue
            if not line.product_id:
                continue
            if line.price_unit <= 0:
                raise ValidationError(
                    _('❌ Preço unitário inválido!\n\n'
                      'Produto: %(product)s\n'
                      'Preço unitário: %(price).2f\n\n'
                      '💡 O preço unitário deve ser maior que zero.'
                    ) % {
                        'product': line.product_id.display_name,
                        'price': line.price_unit,
                    }
                )

    def _validate_discount_limit(self):
        """Validação de desconto (chamada ao confirmar pedido)"""
        discount_limit = float(self.env['ir.config_parameter'].sudo().get_param(
            'mh_sale.sale_discount_limit', default=5.0
        ))

        for line in self:
            if not line.order_id.env.user.has_group('sale.group_discount_per_so_line'):
                continue
            if not line.discount or not line.product_id:
                continue

            is_admin = line.env.user.has_group('base.group_system') or \
                       line.env.user.has_group('sales_team.group_sale_manager')

            if not is_admin and line.discount > discount_limit:
                raise ValidationError(
                    _('❌ Desconto não permitido!\n\n'
                      'Produto: %(product)s\n'
                      'Desconto aplicado: %(discount).2f%%\n'
                      'Desconto máximo permitido: %(limit).2f%%\n\n'
                      '💡 Reduza o desconto ou solicite aprovação.'
                    ) % {
                        'product': line.product_id.display_name,
                        'discount': line.discount,
                        'limit': discount_limit
                    }
                )

    def _validate_quantity_positive(self):
        """Validação de quantidade (chamada ao confirmar pedido)"""
        for line in self:
            if line.display_type:
                continue
            if not line.product_id:
                continue
            if line.product_uom_qty <= 0:
                raise ValidationError(
                    _('❌ Quantidade inválida!\n\n'
                      'Produto: %(product)s\n'
                      'Quantidade: %(qty).2f\n\n'
                      '💡 A quantidade deve ser maior que zero.'
                    ) % {
                        'product': line.product_id.display_name,
                        'qty': line.product_uom_qty,
                    }
                )

    @api.onchange('product_id')
    def _onchange_product_lot_clear(self):
        """Clear lot when product changes and update price"""

        # Se não há produto, limpa tudo
        if not self.product_id:
            self.lot_id = False
            self.product_uom_qty = 0
            self.length = 0.0
            self.width = 0.0
            self.thickness = 0.0
            self.units_qty = 1
            self.price_unit = 0
            self._compute_quantity_from_dimensions()
            return

        product_form = self.product_id.product_form if hasattr(self.product_id, 'product_form') else 'none'

        if product_form == 'none':
            # Produto simples: SEMPRE limpa tudo e atualiza preço
            self.lot_id = False
            self.product_uom_qty = 0
            self.length = 0.0
            self.width = 0.0
            self.thickness = 0.0
            self.units_qty = 1
            self.price_unit = self.product_id.lst_price
            self._compute_quantity_from_dimensions()
        else:
            # Produto dimensional
            if self.lot_id:
                # TEM lote preenchido
                if self.lot_id.product_id != self.product_id:
                    # Lote incompatível: Limpa tudo
                    self.lot_id = False
                    self.product_uom_qty = 0
                    self.length = 0.0
                    self.width = 0.0
                    self.thickness = 0.0
                    self.units_qty = 1
                    self.price_unit = 0
                    self._compute_quantity_from_dimensions()
                else:
                    self.lot_id = self.lot_id
                    self._onchange_lot_id()
            else:
                # NÃO tem lote: preparar para cotação manual.
                # Limpar dimensões editáveis, mas preencher espessura e preço
                # a partir do template (slab/strip/tiles usam thickness fixo;
                # block espera entrada manual do user para thickness).
                self.lot_id = False
                self.product_uom_qty = 0
                self.length = 0.0
                self.width = 0.0
                if product_form == 'block':
                    self.thickness = 0.0
                else:
                    self.thickness = self.product_id.thickness or 0.0
                self.units_qty = 1
                self.price_unit = self.product_id.lst_price or 0.0
                self._compute_quantity_from_dimensions()
        

    @api.depends('product_id', 'lot_id', 'product_uom_qty', 'order_id.warehouse_id', 'order_id.order_line.product_uom_qty')
    def _compute_qty_at_date(self):
        """Override to consider lot availability when lot is selected"""
        # Group lines by order for efficient processing
        for order in self.mapped('order_id'):
            order_lines = self.filtered(lambda l: l.order_id == order)

            # Build a dictionary of quantities already considered per product/lot
            quantities_per_product_lot = {}

            # Process each line in the order
            for line in order_lines:
                if not line.product_id:
                    line.virtual_available_at_date = 0
                    line.free_qty_today = 0
                    line.qty_available_today = 0
                    line.scheduled_date = fields.Datetime.now()
                    line.forecast_expected_date = fields.Datetime.now()
                    line.qty_to_deliver = 0
                    continue

                # Calculate quantity already "used" by other lines before this one
                other_lines_qty = 0

                # Create a list index for proper ordering
                line_index_map = {l: i for i, l in enumerate(order_lines)}
                current_line_index = line_index_map.get(line, 0)

                for other_line in order_lines:
                    # Skip self and lines without product
                    if other_line == line or not other_line.product_id:
                        continue

                    # Check if it's the same product/lot combination
                    same_product = other_line.product_id == line.product_id
                    same_lot = (line.lot_id and other_line.lot_id == line.lot_id) or (not line.lot_id and not other_line.lot_id)

                    if same_product and same_lot:
                        # Only count lines that appear before this one in the order
                        other_line_index = line_index_map.get(other_line, 0)
                        if other_line_index < current_line_index:
                            other_lines_qty += other_line.product_uom_qty

                if line.lot_id:
                    # Get warehouse from order
                    warehouse = order.warehouse_id

                    # Skip if lot_id is a NewId (unsaved record)
                    # This happens when creating new lines
                    if not isinstance(line.lot_id.id, int):
                        line.virtual_available_at_date = 0
                        line.free_qty_today = 0
                        line.qty_available_today = 0
                        line.scheduled_date = fields.Datetime.now()
                        line.forecast_expected_date = fields.Datetime.now()
                        line.qty_to_deliver = line.product_uom_qty
                        continue

                    # Search for available quantity of the specific lot
                    domain = [
                        ('lot_id', '=', line.lot_id.id),
                        ('location_id.usage', '=', 'internal'),
                    ]

                    # Add warehouse filter if available
                    if warehouse:
                        domain.append(('location_id.warehouse_id', '=', warehouse.id))

                    quants = self.env['stock.quant'].search(domain)

                    # Calculate available quantity (quantity - reserved)
                    available = sum(quants.mapped(lambda q: q.quantity - q.reserved_quantity))

                    # Subtract quantity already allocated to other lines
                    available_for_line = max(0, available - other_lines_qty)

                    # Set the fields used by qty_at_date widget
                    line.virtual_available_at_date = available_for_line
                    line.free_qty_today = available_for_line
                    line.qty_available_today = available_for_line
                    line.scheduled_date = fields.Datetime.now()
                    line.forecast_expected_date = fields.Datetime.now()

                    # Set qty_to_deliver for proper widget calculation
                    if line.state == 'sale':
                        line.qty_to_deliver = line.product_uom_qty - line.qty_delivered
                    else:
                        line.qty_to_deliver = line.product_uom_qty
                else:
                    # Product without lot - check general availability
                    warehouse = order.warehouse_id
                    product = line.product_id.with_context(
                        warehouse=warehouse.id if warehouse else False
                    )
                    available = product.virtual_available

                    # Subtract quantity already allocated to other lines
                    available_for_line = max(0, available - other_lines_qty)

                    # Set the fields
                    line.virtual_available_at_date = available_for_line
                    line.free_qty_today = available_for_line
                    line.qty_available_today = available_for_line
                    line.scheduled_date = fields.Datetime.now()
                    line.forecast_expected_date = fields.Datetime.now()

                    if line.state == 'sale':
                        line.qty_to_deliver = line.product_uom_qty - line.qty_delivered
                    else:
                        line.qty_to_deliver = line.product_uom_qty
    
    def _update_price_from_lot(self):
        """
        Atualiza o preço baseado no lote selecionado.

        CRITICAL: Respeita o context flag 'skip_lot_price_update'.
        Quando skip_lot_price_update=True, NÃO atualiza o preço.

        Isso permite que o módulo mh_sale_pricelist_lot preencha dimensões
        sem sobrescrever o preço calculado pelo pricelist.
        """
        # CRITICAL: Check context flag before updating price
        if self.env.context.get('skip_lot_price_update'):
            return  # Skip price update, keep current price_unit

        # Fluxo Stone Trading (MZ): nas empresas em standard (Portugal) nao se aplica.
        order = self.order_id or self.env['sale.order'].browse(self.env.context.get('order_id'))
        if order and not order._mh_stone_gates_apply():
            return

        if self.lot_id and hasattr(self.lot_id, 'list_price_lot'):
            # Usar preço específico do lote (mesmo que seja 0)
            self.price_unit = self.lot_id.list_price_lot
        elif self.product_id:
            # Fallback: usar preço do produto se não há lote ou lote sem preço
            self.price_unit = self.product_id.lst_price

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        """Atualiza o preço e dimensões quando um lote é selecionado"""
        self._update_price_from_lot()

        # Preencher dimensões do lote se aplicável
        if self.lot_id:
            product_form = self.product_id.product_form if self.product_id and hasattr(self.product_id, 'product_form') else 'none'

            if product_form in ['block','slab', 'strip', 'tiles']:
                # Preencher espessura do lote (se existirem)
                if hasattr(self.lot_id, 'length'):
                    self.length = self.lot_id.length
                if hasattr(self.lot_id, 'width'):
                    self.width = self.lot_id.width
                if hasattr(self.lot_id, 'thickness'):
                    if product_form == 'block':
                        self.thickness = self.lot_id.thickness
                    else:
                        self.thickness = self.product_id.thickness

                # Calcular quantidade automaticamente
                self._compute_quantity_from_dimensions()
        else:
            self.length = 0.0
            self.width = 0.0
            self.thickness = 0.0
            # Calcular quantidade automaticamente
            self._compute_quantity_from_dimensions()

    @api.onchange('length', 'width', 'thickness', 'units_qty')
    def _onchange_dimensions(self):
        self._compute_quantity_from_dimensions()

    def _compute_quantity_from_dimensions(self):
        """Calcula product_uom_qty baseado nas dimensões e product_form"""
        if not self.product_id:
            return

        product_form = self.product_id.product_form if hasattr(self.product_id, 'product_form') else 'none'
        units_qty = self.units_qty or 1  # Default 1 se vazio

        if product_form == 'block':
            # Volume total (m³) = comprimento × largura × espessura × unidades
            if self.length > 0  and self.width > 0 and self.thickness > 0:
                calculated = self.length * self.width * self.thickness * units_qty
                # Arredondar com precision do UOM
                if self.product_uom:
                    self.product_uom_qty = float_round(calculated, precision_rounding=self.product_uom.rounding)
                else:
                    self.product_uom_qty = calculated
            else:
                self.product_uom_qty = 0.0

        elif product_form in ['slab', 'strip', 'tiles']:
            # Área total (m²) = comprimento × largura × unidades
            if self.length > 0 and self.width > 0:
                calculated = self.length * self.width * units_qty
                # Arredondar com precision do UOM
                if self.product_uom:
                    self.product_uom_qty = float_round(calculated, precision_rounding=self.product_uom.rounding)
                else:
                    self.product_uom_qty = calculated
            else:
                self.product_uom_qty = 0.0
        else:
            # product_form = 'none': quantidade = units_qty
            if self.product_uom:
                self.product_uom_qty = float_round(self.units_qty, precision_rounding=self.product_uom.rounding)
            else:
                self.product_uom_qty = self.units_qty

    @api.depends('state')
    def _compute_product_uom_readonly(self):
        """Sobrescrever para tornar product_uom SEMPRE readonly"""
        for line in self:
            line.product_uom_readonly = True

    def action_open_stock_wizard(self):
        """Abrir wizard de seleção de estoque disponível

        Método chamado do botão no <control> da lista de order_line.
        Segue o padrão do Odoo (similar a action_add_from_catalog).
        """
        order = self.env['sale.order'].browse(self.env.context.get('order_id'))
        return order.action_open_stock_wizard()

    @api.depends('product_id.product_form', 'lot_id', 'order_id.state')
    def _compute_lot_editable(self):
        """Computar editabilidade de campos relativos a forma do produto.

        - lot_editable: lote pode ser editado (product_form != 'none')
        - thickness_editable: bloco normal OU produto dimensional em cotação manual
        - units_qty_editable: produto simples OU cotação manual sem lote
        - dimensions_editable: cotação manual (draft/sent, dimensional, sem lote)
        """
        for line in self:
            if line.product_id and hasattr(line.product_id, 'product_form'):
                pf = line.product_id.product_form
                state = line.order_id.state if line.order_id else 'draft'
                # Cotação manual: produto dimensional, sem lote, em draft/sent
                manual_quote = (
                    pf in ('block', 'slab', 'strip', 'tiles')
                    and not line.lot_id
                    and state in ('draft', 'sent')
                )
                line.lot_editable = pf != 'none'
                line.thickness_editable = pf == 'block' or (manual_quote and pf == 'block')
                line.units_qty_editable = pf == 'none' or manual_quote
                line.dimensions_editable = manual_quote
            else:
                # Se não tem product_form, considerar editável
                line.lot_editable = True
                line.thickness_editable = True
                line.units_qty_editable = True
                line.dimensions_editable = False

    def _compute_can_edit_price(self):
        """Computar se o utilizador pode editar o preço unitário"""
        has_permission = self.env.user.has_group('mh_sale.group_sale_price_edit')
        for line in self:
            line.can_edit_price = has_permission

    def _prepare_invoice_line(self, **kwargs):
        """Override para passar lot_id e dimensões para a linha da fatura"""
        res = super()._prepare_invoice_line(**kwargs)
        if self.lot_id:
            res['lot_id'] = self.lot_id.id
        # Passar campos de dimensão
        res.update({
            'units_qty': self.units_qty,
            'length': self.length,
            'width': self.width,
            'thickness': self.thickness,
        })
        return res