from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.osv import expression


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Estende `name_search` para incluir valores de atributos de variante
        (PN, Polido, etc.) na pesquisa multi-palavra.

        Em Odoo 18, `product.product.name_search` faz pesquisa custom em
        `default_code` + `name` sem fallback a `display_name`/`_search_display_name`,
        por isso "Slab NG Stone PN" não devolve nada (PN é atributo de variante,
        não está em `name`/`default_code`).

        Algoritmo: para multi-palavra positivo, faz primeiro o super() para
        manter heurísticas standard (code/barcode/[ref]); se nada vier,
        divide por espaços e cada pedaço tem de bater em
        `name | default_code | attribute_value`; AND entre pedaços.
        """
        result = super().name_search(name=name, args=args, operator=operator, limit=limit)
        if (result
                or not name
                or operator not in ('ilike', 'like', '=ilike', '=like')):
            return result

        # Sem matches no super: tentar pesquisa por palavras incluindo
        # valores de atributos de variante. Funciona tanto para single-word
        # ("PN") como para multi-palavra ("Slab NG Stone PN").
        pieces = [p for p in name.split() if p]
        per_piece = []
        for p in pieces:
            per_piece.append([
                '|', '|',
                ('name', operator, p),
                ('default_code', operator, p),
                ('product_template_attribute_value_ids.name', operator, p),
            ])
        domain = expression.AND([args or [], expression.AND(per_piece)])
        products = self.search_fetch(domain, ['display_name'], limit=limit)
        return [(p.id, p.display_name) for p in products.sudo()]

    # Campo PCMP computed a partir das SVLs (definido em mh_stock_valuation)
    # min_display_digits (Odoo 18 standard pattern) — storage com precisão total
    # (NUMERIC sem rounding), exibição mín. 2 decimais. Evita drift AVCO.
    pcmp = fields.Float(
        string='PCMP',
        min_display_digits='Product Price',
        default=0.0,
        help="Preço de Custo Médio Ponderado calculado automaticamente das SVLs. "
             "Armazenado com precisão total; exibido com mín. 2 decimais."
    )

    use_manual_pricing = fields.Boolean(
        string='Preço Manual',
        default=False,
        help='Activar para fixar manualmente o preço de venda da variante. '
             'Quando activo, o preço fica preservado e a margem ajusta-se automaticamente '
             'quando o PCMP muda. Quando inactivo, recalcula de PCMP × (1 + margem/100).'
    )

    custom_lst_price = fields.Float(
        string='Preço de Venda da Variante',
        digits='Product Price',
        help='Preço de venda específico desta variante. Se não definido, usa o preço do template.',
        company_dependent=True
    )

    use_variant_price = fields.Boolean(
        string='Usa Preço Próprio',
        readonly=True,
        help='Marque para usar preço de venda independente para esta variante'
    )

    lst_price = fields.Float(
        string='Preço de Venda Final',
        compute='_compute_lst_price',
        digits='Product Price',
        help='Preço de venda final incluindo extras de atributos.',
        store=True
    )

    # Override the list_price field to use our logic
    list_price = fields.Float(
        string='Preço de Venda',
        compute='_compute_product_list_price',
        inverse='_inverse_product_list_price',
        digits='Product Price',
        help='Preço de venda do produto. Para variantes, pode ser independente do template.',
        store=True
    )

    variant_description = fields.Char(
        string='Descrição Variante',
        compute='_compute_variant_description',
        store=True,
        index=True,
        help="Descrição dos atributos da variante para facilitar pesquisa"
    )

    # Margin Management for Variants
    margin = fields.Float(
        string="Margem da Variante (%)",
        compute='_compute_margin',
        inverse='_inverse_margin',
        store=True,
        help="Margem de lucro da variante. Para product_form='none' recalcula automaticamente "
             "de (custom_lst_price - pcmp)/pcmp × 100 quando pcmp muda."
    )

    use_variant_margin = fields.Boolean(
        string="Usar Margem Própria",
        readonly=True,
        help="Marque para usar margem independente para esta variante"
    )

    margin_status = fields.Selection([
        ('low', 'Margem Baixa'),
        ('normal', 'Margem Normal'),
        ('high', 'Margem Alta')
    ], string="Status da Margem", compute='_compute_margin_status')

    margin_amount = fields.Monetary(
        string="Valor da Margem",
        compute='_compute_margin_analysis'
    )

    effective_margin = fields.Float(
        string="Margem Efetiva (%)",
        compute='_compute_effective_margin',
        help="Margem considerando se usa própria ou do template"
    )

    # Campos herdados do template (related)
    product_family_id = fields.Many2one(
        'product.family',
        string='Família',
        related='product_tmpl_id.product_family_id',
        store=True,
        readonly=False,
        help='Família à qual este produto pertence'
    )

    business_segment_id = fields.Many2one(
        'business.segment',
        string='Segmento de Negócio',
        related='product_tmpl_id.business_segment_id',
        store=True,
        readonly=False,
        help='Segmento de negócio deste produto'
    )

    product_classification = fields.Selection(
        related='product_tmpl_id.product_classification',
        string='Classificação do Artigo',
        store=True,
        readonly=False,
        help='Classificação do produto para fins contabilísticos e fiscais')

    product_form = fields.Selection(
        related='product_tmpl_id.product_form',
        string='Forma do Produto',
        store=True,
        readonly=True,
        help='Forma física do produto (Bloco, Placa, Banda, etc.)'
    )
    
    @api.depends('product_template_variant_value_ids', 'product_template_attribute_value_ids')
    def _compute_variant_description(self):
        """Compute variant description from attribute values"""
        for product in self:
            if product.product_template_attribute_value_ids:
                # Obter os valores dos atributos da variante
                values = []
                for ptav in product.product_template_attribute_value_ids:
                    attr_value = ptav.name
                    values.append(attr_value)
                product.variant_description = ' '.join(values)
            elif product.product_template_variant_value_ids:
                # Fallback para product_template_variant_value_ids
                values = []
                for ptvv in product.product_template_variant_value_ids:
                    attr_value = ptvv.name
                    values.append(attr_value)
                product.variant_description = ' '.join(values)
            else:
                product.variant_description = False

    @api.depends('custom_lst_price', 'use_variant_price', 'product_tmpl_id.list_price')
    def _compute_product_list_price(self):
        """Override list_price computation to use variant price when enabled"""
        for product in self:
            if product.use_variant_price and product.custom_lst_price > 0:
                product.list_price = product.custom_lst_price
            else:
                product.list_price = product.product_tmpl_id.list_price

    def _inverse_product_list_price(self):
        """Handle inverse operation for list_price"""
        for product in self:
            if product.use_variant_price:
                product.custom_lst_price = product.list_price
            else:
                # Only update template if this is the only variant or user explicitly wants it
                if len(product.product_tmpl_id.product_variant_ids) == 1:
                    product.product_tmpl_id.list_price = product.list_price

    @api.depends('custom_lst_price', 'use_variant_price', 'list_price')
    def _compute_lst_price(self):
        """Ensure lst_price also reflects our variant pricing"""
        for product in self:
            # Start with list_price (which now includes our variant logic)
            price = product.list_price
            # Add any attribute extras (maintaining compatibility)
            price += product._get_attributes_extra_price()
            product.lst_price = price

    def _search_product_lst_price(self, operator, value):
        """Search method for lst_price considering variant prices"""
        products_with_variant_price = self.search([
            ('use_variant_price', '=', True),
            ('custom_lst_price', operator, value)
        ])

        templates = self.env['product.template'].search([
            ('list_price', operator, value)
        ])
        products_from_templates = self.search([
            ('product_tmpl_id', 'in', templates.ids),
            ('use_variant_price', '=', False)
        ])

        return [('id', 'in', (products_with_variant_price | products_from_templates).ids)]

    def price_compute(self, price_type, uom=False, currency=False, company=None):
        """Override price computation to handle variant prices"""
        if price_type == 'list_price':
            prices = {}
            for product in self:
                if product.use_variant_price and product.custom_lst_price > 0:
                    price = product.custom_lst_price
                else:
                    price = product.product_tmpl_id.list_price

                # Apply UOM conversion if needed
                if uom and price:
                    price = product.uom_id._compute_price(price, uom)

                # Apply currency conversion if needed
                if currency and price:
                    price = product.currency_id._convert(
                        price, currency, company or self.env.company,
                        fields.Date.today()
                    )

                prices[product.id] = price
            return prices
        else:
            return super().price_compute(price_type, uom=uom, currency=currency, company=company)

    @api.model_create_multi
    def create(self, vals_list):
        """Ensure proper price handling on variant creation"""
        if self.env.user.has_group('mh_inventory.group_block_product_create'):
            raise ValidationError('Não tem permissão para criar artigos. Contacte o administrador.')
        products = super().create(vals_list)
        for product in products:
            if product.use_variant_price and product.custom_lst_price:
                # Trigger the price computation
                product._compute_product_list_price()

        return products

    @api.depends('margin', 'use_variant_margin', 'product_tmpl_id.margin')
    def _compute_effective_margin(self):
        """Calcula a margem efetiva da variante"""
        for product in self:
            if product.use_variant_margin:
                product.effective_margin = product.margin
            else:
                product.effective_margin = product.product_tmpl_id.margin

    @api.depends('effective_margin')
    def _compute_margin_status(self):
        """Classifica a margem baseada nas configurações do usuário"""
        ICP = self.env['ir.config_parameter'].sudo()
        low_threshold = float(ICP.get_param('mh_inventory.margin_low_threshold', 10.0))
        high_threshold = float(ICP.get_param('mh_inventory.margin_high_threshold', 50.0))

        for product in self:
            if product.effective_margin < low_threshold:
                product.margin_status = 'low'
            elif product.effective_margin > high_threshold:
                product.margin_status = 'high'
            else:
                product.margin_status = 'normal'

    @api.depends('list_price', 'pcmp')
    def _compute_margin_analysis(self):
        """Calcula valores de análise da margem"""
        for product in self:
            if product.list_price and product.pcmp:
                product.margin_amount = product.list_price - product.pcmp
            else:
                product.margin_amount = 0.0



    @api.depends('pcmp', 'custom_lst_price', 'use_variant_price', 'use_variant_margin', 'use_manual_pricing')
    def _compute_margin(self):
        """Calcula margem da variante:
        - use_manual_pricing=True + use_variant_price + use_variant_margin:
          margin = (custom_lst_price - pcmp)/pcmp × 100 (auto, quando pcmp muda).
        - Outros casos: preserva valor stored (user define manualmente).
        """
        for product in self:
            if (product.use_manual_pricing
                    and product.use_variant_price and product.use_variant_margin
                    and product.pcmp and product.pcmp > 0
                    and product.custom_lst_price and product.custom_lst_price > 0):
                product.margin = ((product.custom_lst_price - product.pcmp) / product.pcmp) * 100
            else:
                # Preservar stored
                if product.id:
                    self.env.cr.execute(
                        "SELECT margin FROM product_product WHERE id = %s", (product.id,)
                    )
                    result = self.env.cr.fetchone()
                    product.margin = result[0] if result and result[0] else 0.0
                else:
                    product.margin = 0.0

    def _inverse_margin(self):
        """User edita margin manualmente:
        - use_manual_pricing=True + use_variant_price + use_variant_margin:
          recalcula custom_lst_price = pcmp × (1 + margin/100).
        Bloqueia se user gravar margem negativa (apenas em variantes com use_variant_margin).
        """
        for product in self:
            if product.use_variant_margin and product.margin < 0:
                raise ValidationError(
                    f"Variante '{product.name}':\n"
                    f"Margem ({product.margin:.2f}%) não pode ser negativa."
                )
            if (product.use_manual_pricing
                    and product.use_variant_price and product.use_variant_margin
                    and product.pcmp and product.pcmp > 0 and product.margin):
                product.custom_lst_price = product.pcmp * (1 + product.margin / 100)

    @api.onchange('list_price')
    def _onchange_list_price_variant(self):
        """User altera list_price na UI (variante use_variant_price):
        Atualiza custom_lst_price e margin em tempo real.
        """
        if (self.use_variant_price
                and self.list_price and self.list_price > 0):
            self.custom_lst_price = self.list_price
            if self.use_variant_margin and self.pcmp and self.pcmp > 0:
                self.margin = ((self.list_price - self.pcmp) / self.pcmp) * 100

    @api.onchange('use_manual_pricing')
    def _onchange_use_manual_pricing_variant(self):
        """Ao activar 'Preço Manual', captura o custom_lst_price actual."""
        if self.use_manual_pricing and self.list_price and self.list_price > 0:
            if self.use_variant_price:
                self.custom_lst_price = self.list_price

    # Constraint @api.constrains('margin') removida: bloqueava recomputes
    # automáticos de margem negativa (ex.: recepção de compra com custo > preço).
    # Validação migrada para _inverse_margin — só dispara quando o user escreve
    # directamente margin na view.

    def write(self, vals):
        """Handle price updates properly"""
        result = super().write(vals)

        if 'use_variant_price' in vals or 'custom_lst_price' in vals or 'margin' in vals:
            for product in self:
                product._compute_product_list_price()

        return result
