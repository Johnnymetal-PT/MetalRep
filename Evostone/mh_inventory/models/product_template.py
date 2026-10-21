from odoo import models, fields, api
from odoo.tools import float_compare
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # ========================================
    # CLASSIFICAÇÃO DO PRODUTO
    # ========================================

    product_classification = fields.Selection([
        ('raw_material', 'Matéria Prima'),
        ('auxiliary_material', 'Material Auxiliar'),
        ('packaging_material', 'Material Embalagem'),
        ('fixed_asset', 'Imobilizado/Consumivel'),
        ('finished_product', 'Produto Acabado'),
        ('merchandise', 'Mercadoria'),
        ('purchase_service', 'Serviço de Compra'),
        ('sale_service', 'Serviço de Venda'),
        ('service', 'Serviço'),
        ('other', 'Outros'),
    ], string='Classificação do Artigo', required=True, default='other',
       tracking=True,                                              
       help='Classificação do produto para fins contabilísticos e fiscais')

    # ========================================
    # FORMA DO PRODUTO (para transformações)
    # ========================================

    product_form = fields.Selection([
        ('none', 'Nenhum'),
        ('block', 'Bloco'),
        ('slab', 'Placa'),
        ('strip', 'Banda'),
        ('tiles', 'Ladrilhos')
    ], string='Forma do Produto', required=True, default='none',
       help='Define a forma do produto: Bloco pode virar Placa, Placa pode virar Banda')

    density = fields.Float(
        string='Densidade (kg/m³)',
        digits=(10, 2),
        help='Densidade do material em kg/m³ para cálculo de peso a partir das '
             'dimensões (peso = L × W × T × densidade). Se vazio, usa o '
             'campo Empresa → Densidade Padrão de Pedra '
             '(default: 2700 kg/m³).',
    )

    # ========================================
    # PREÇOS CUSTOMIZADOS POR VARIANTE
    # ========================================

    use_custom_variant_pricing = fields.Boolean(
        string='Preços Personalizados',
        compute='_compute_use_custom_variant_pricing',
        store=True,
        readonly=True,
        help="Ativado quando o produto tem variantes"
    )

    # Margin Management Fields
    margin = fields.Float(
        string="Margem (%)",
        compute='_compute_margin',
        inverse='_inverse_margin',
        store=True,
        help="Margem de lucro (%). Para product_form='none' recalcula automaticamente "
             "de (manual_list_price - pcmp)/pcmp × 100 quando pcmp muda."
    )

    margin_status = fields.Selection([
        ('low', 'Margem Baixa'),
        ('normal', 'Margem Normal'),
        ('high', 'Margem Alta')
    ], string="Status da Margem", compute='_compute_margin_status')

    margin_amount = fields.Monetary(
        string="Valor da Margem",
        compute='_compute_margin_analysis',
        help="Valor absoluto da margem de lucro"
    )

    pcmp = fields.Float(
        string='PCMP',
        compute='_compute_pcmp',
        inverse='_set_pcmp',
        min_display_digits='Product Price',
        help='Preço Custo Médio Ponderado. Se tem 1 variante, herda da variante. Com múltiplas variantes, é 0.0. '
             'Armazenado com precisão total (Odoo 18 standard pattern para AVCO).'
    )

    # Toggle: quando True, list_price é manual (lido de manual_list_price) e
    # margin recalcula automaticamente quando pcmp muda. Quando False, list_price
    # é recalculado de pcmp × (1 + margin/100) (comportamento clássico).
    use_manual_pricing = fields.Boolean(
        string='Preço Manual',
        default=False,
        help='Activar para fixar manualmente o preço de venda. Quando activo, '
             'o preço fica preservado e a margem ajusta-se automaticamente quando '
             'o PCMP muda. Quando inactivo, o preço recalcula-se de PCMP × (1 + margem/100).'
    )

    # Valor manual do preço de venda. Plain stored (sem compute) — fonte estável
    # que evita ciclos de recompute entre list_price e margin.
    manual_list_price = fields.Float(
        string='Preço Venda Manual',
        store=True,
        digits='Product Price',
        help='Valor manual do preço de venda quando use_manual_pricing=True. '
             'Definido pelo inverse de list_price ou margin.'
    )

    # Override list_price para templates sem variantes customizadas
    list_price = fields.Float(
        compute='_compute_list_price_with_margin',
        inverse='_inverse_list_price_with_margin',
        store=True,
        string="Preço de Venda",
    )

    # Campos de Família e Negócio
    product_family_id = fields.Many2one(
        'product.family',
        string='Família',
        help='Família à qual este produto pertence'
    )

    business_segment_id = fields.Many2one(
        'business.segment',
        string='Segmento de Negócio',
        help='Segmento de negócio deste produto'
    )
    
    @api.depends('product_variant_count', 'attribute_line_ids', 'product_variant_ids.product_template_attribute_value_ids')
    def _compute_use_custom_variant_pricing(self):
        """Automatically enable custom variant pricing when product has multiple variants"""
        for template in self:
            # Enable if product has more than 1 variant AND has configurable attributes
            # OR if single variant has attribute values
            if template.product_variant_count > 1 and bool(template.attribute_line_ids):
                use_custom_price = True
            elif template.product_variant_count == 1 and bool(template.attribute_line_ids):
                # Check if the single variant has attribute values
                variant = template.product_variant_ids[0] if template.product_variant_ids else False
                use_custom_price = bool(variant and variant.product_template_attribute_value_ids)
            else:
                use_custom_price = False

            template.use_custom_variant_pricing = use_custom_price
            template.product_variant_ids.write({'use_variant_price': use_custom_price, 'use_variant_margin': use_custom_price})

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.user.has_group('mh_inventory.group_block_product_create'):
            raise ValidationError('Não tem permissão para criar artigos. Contacte o administrador.')
        templates = super().create(vals_list)
        for template in templates:
            template._compute_use_custom_variant_pricing()
        return templates

    def write(self, vals):
        result = super().write(vals)
        if 'product_variant_ids' in vals or 'attribute_line_ids' in vals:
            # Recalcula quando variantes são criadas/modificadas
            for template in self:
                template._compute_use_custom_variant_pricing()
        return result

    @api.depends('margin')
    def _compute_margin_status(self):
        """Classifica a margem baseada nas configurações do usuário"""
        ICP = self.env['ir.config_parameter'].sudo()
        low_threshold = float(ICP.get_param('mh_inventory.margin_low_threshold', 10.0))
        high_threshold = float(ICP.get_param('mh_inventory.margin_high_threshold', 50.0))

        for template in self:
            if template.margin < low_threshold:
                template.margin_status = 'low'
            elif template.margin > high_threshold:
                template.margin_status = 'high'
            else:
                template.margin_status = 'normal'

    @api.depends('product_variant_ids', 'product_variant_ids.pcmp', 'product_variant_count')
    def _compute_pcmp(self):
        """Calcula PCMP do template baseado nas variantes"""
        for template in self:
            if template.use_custom_variant_pricing == False:
                # Única variante: herdar PCMP da variante
                variant = template.product_variant_ids[0] if template.product_variant_ids else False
                template.pcmp = variant.pcmp if variant else 0.0
            else:
                # Múltiplas variantes: sempre 0.0
                template.pcmp = 0.0

    def _set_pcmp(self):
        """O PCMP da variante é agora computed - não pode ser definido manualmente.

        O PCMP é calculado automaticamente a partir das SVLs (Stock Valuation Layers).
        Este método existe apenas por compatibilidade com o inverse do campo.
        """
        # PCMP é computed - não fazer nada
        pass

    @api.depends('list_price', 'pcmp', 'margin')
    def _compute_margin_analysis(self):
        """Calcula valores de análise da margem"""
        for template in self:
            if template.list_price and template.pcmp:
                template.margin_amount = template.list_price - template.pcmp
            else:
                template.margin_amount = 0.0

    @api.depends('pcmp', 'margin', 'manual_list_price', 'use_manual_pricing')
    def _compute_list_price_with_margin(self):
        """Calcula list_price:
        - use_manual_pricing=True: lê de manual_list_price (preservado quando pcmp muda).
        - use_manual_pricing=False: list_price = pcmp × (1+margin/100) (comportamento clássico).
        """
        for template in self:
            if template.use_custom_variant_pricing:
                continue
            if template.use_manual_pricing:
                # Modo manual: list_price = manual_list_price (preservado)
                if template.manual_list_price and template.manual_list_price > 0:
                    template.list_price = template.manual_list_price
                elif template.pcmp and template.margin:
                    # Inicialização quando user activa modo manual sem ter valor stored
                    template.list_price = template.pcmp * (1 + template.margin / 100)
                elif template.pcmp:
                    template.list_price = template.pcmp
            else:
                # Modo automático: pcmp × (1 + margin/100)
                if template.pcmp and template.margin:
                    template.list_price = template.pcmp * (1 + template.margin / 100)

    def _inverse_list_price_with_margin(self):
        """User edita list_price:
        - use_manual_pricing=True: copia para manual_list_price + recalcula margin.
        - use_manual_pricing=False: recalcula só margin.
        Bloqueia se o preço gravado produzir margem negativa (custo > preço).
        """
        for template in self:
            if template.use_custom_variant_pricing:
                continue
            if template.list_price and template.list_price > 0:
                if template.pcmp and template.pcmp > 0:
                    new_margin = ((template.list_price - template.pcmp) / template.pcmp) * 100
                    if new_margin < 0:
                        raise ValidationError(
                            f"Artigo '{template.name}':\n"
                            f"Preço de venda ({template.list_price:.2f}) inferior ao custo "
                            f"({template.pcmp:.2f}). Margem ficaria negativa."
                        )
                    template.margin = new_margin
                if template.use_manual_pricing:
                    template.manual_list_price = template.list_price

    @api.depends('use_custom_variant_pricing', 'pcmp', 'manual_list_price', 'use_manual_pricing')
    def _compute_margin(self):
        """Calcula margem:
        - use_manual_pricing=True: margin = (manual_list_price - pcmp)/pcmp × 100 (auto).
        - use_manual_pricing=False: preserva valor stored (user define manualmente).
        """
        for template in self:
            if (template.use_manual_pricing
                    and not template.use_custom_variant_pricing
                    and template.pcmp and template.pcmp > 0
                    and template.manual_list_price and template.manual_list_price > 0):
                template.margin = ((template.manual_list_price - template.pcmp) / template.pcmp) * 100
            else:
                # Preservar valor stored
                if template.id:
                    self.env.cr.execute(
                        "SELECT margin FROM product_template WHERE id = %s", (template.id,)
                    )
                    result = self.env.cr.fetchone()
                    template.margin = result[0] if result and result[0] else 0.0
                else:
                    template.margin = 0.0

    def _inverse_margin(self):
        """User edita margin manualmente:
        - use_manual_pricing=True: recalcula manual_list_price = pcmp × (1+margin/100).
        - use_manual_pricing=False: nada (margin é o valor primário).
        Bloqueia se user gravar margem negativa.
        """
        for template in self:
            if template.use_custom_variant_pricing:
                continue
            if template.margin < 0:
                raise ValidationError(
                    f"Artigo '{template.name}':\n"
                    f"Margem ({template.margin:.2f}%) não pode ser negativa."
                )
            if (template.use_manual_pricing
                    and template.pcmp and template.pcmp > 0 and template.margin):
                template.manual_list_price = template.pcmp * (1 + template.margin / 100)

    @api.onchange('margin')
    def _onchange_margin_template(self):
        """User altera margin na UI: actualiza list_price em tempo real."""
        if (not self.use_custom_variant_pricing
                and self.pcmp and self.pcmp > 0 and self.margin):
            new_price = self.pcmp * (1 + self.margin / 100)
            if self.use_manual_pricing:
                self.manual_list_price = new_price
            self.list_price = new_price

    @api.onchange('list_price')
    def _onchange_list_price_template(self):
        """User altera list_price na UI: actualiza margin (e manual_list_price se modo manual)."""
        if (not self.use_custom_variant_pricing
                and self.list_price and self.list_price > 0):
            if self.use_manual_pricing:
                self.manual_list_price = self.list_price
            if self.pcmp and self.pcmp > 0:
                self.margin = ((self.list_price - self.pcmp) / self.pcmp) * 100

    @api.onchange('use_manual_pricing')
    def _onchange_use_manual_pricing(self):
        """Ao activar 'Preço Manual', captura o list_price actual como manual_list_price."""
        if self.use_manual_pricing and self.list_price and self.list_price > 0:
            self.manual_list_price = self.list_price

    @api.constrains('product_classification', 'type', 'is_storable', 'sale_ok', 'purchase_ok')
    def _check_classification_type(self):
        """Validar consistência entre classificação e tipo de produto"""
        PHYSICAL_CLASSIFICATIONS = ('raw_material', 'auxiliary_material', 'packaging_material', 'fixed_asset', 'finished_product', 'merchandise')
        for template in self:
            if not template.product_classification:
                continue
            if template.product_classification in ('service', 'purchase_service', 'sale_service') and template.type != 'service':
                raise ValidationError(
                    f"Artigo '{template.name}':\n"
                    f"Classificação 'Serviço' exige tipo de produto 'Serviço'."
                )
            if template.product_classification == 'sale_service':
                if not template.sale_ok:
                    raise ValidationError(
                        f"Artigo '{template.name}':\n"
                        f"Classificação 'Serviço de Venda' exige que 'Pode ser Vendido' esteja activo."
                    )
                if template.purchase_ok:
                    raise ValidationError(
                        f"Artigo '{template.name}':\n"
                        f"Classificação 'Serviço de Venda' não permite que 'Pode ser Comprado' esteja activo."
                    )
            if template.product_classification == 'purchase_service':
                if not template.purchase_ok:
                    raise ValidationError(
                        f"Artigo '{template.name}':\n"
                        f"Classificação 'Serviço de Compra' exige que 'Pode ser Comprado' esteja activo."
                    )
                if template.sale_ok:
                    raise ValidationError(
                        f"Artigo '{template.name}':\n"
                        f"Classificação 'Serviço de Compra' não permite que 'Pode ser Vendido' esteja activo."
                    )
            if template.product_classification in PHYSICAL_CLASSIFICATIONS:
                if template.type == 'service':
                    raise ValidationError(
                        f"Artigo '{template.name}':\n"
                        f"Classificação '{template.product_classification}' não é compatível com tipo 'Serviço'.\n"
                        f"Utilize um tipo armazenável."
                    )
                if not template.is_storable:
                    raise ValidationError(
                        f"Artigo '{template.name}':\n"
                        f"Classificação '{template.product_classification}' exige que o artigo seja armazenável."
                    )

    # Constraint @api.constrains('margin') removida: bloqueava recomputes automáticos
    # de margem negativa (ex.: recepção de compra com custo > preço de venda).
    # Validação migrada para _inverse_list_price_with_margin e _inverse_margin —
    # só dispara quando o user escreve directamente list_price ou margin na view.

    @api.model
    def _get_product_price(self, product, qty=1.0, partner=False, pricelist=False):
        if product.use_variant_price and product.custom_lst_price > 0:
            return product.custom_lst_price
        return super()._get_product_price(product, qty=qty, partner=partner, pricelist=pricelist)
