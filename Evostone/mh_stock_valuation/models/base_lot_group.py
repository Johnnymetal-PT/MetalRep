# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools import float_is_zero
from odoo.exceptions import ValidationError
from markupsafe import Markup
import logging

_logger = logging.getLogger(__name__)


class BaseLotGroup(models.Model):
    _name = 'base.lot.group'
    _description = 'Grupo de Lote para Valorização PCMP'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'product_id, base_lot_name'
    _rec_name = 'display_name'

    # ========================================
    # IDENTIFICAÇÃO
    # ========================================

    name = fields.Char(
        string='Nome do Grupo',
        compute='_compute_name',
        store=True,
        readonly=True,
        help='Nome gerado automaticamente baseado em nome base do lote e produto'
    )

    base_lot_name = fields.Char(
        string='Nome Base do Lote',
        required=True,
        readonly=True,
        index=True,
        tracking=True,
        help='Nome base que agrupa todos os lotes (ex: "LOTE_CARRARA")'
    )

    product_id = fields.Many2one(
        'product.product',
        string='Produto',
        required=True,
        readonly=True,
        ondelete='cascade',
        index=True,
        help='Produto associado a este grupo base'
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

    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        default=lambda self: self.env.company,
        required=True,
    )

    currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        string='Moeda',
        readonly=True,
    )

    display_name = fields.Char(
        compute='_compute_display_name',
        store=True,
    )

    # ========================================
    # VALORIZAÇÃO PCMP / SVL
    # ========================================

    # Campos computados de SVL
    quantity_svl = fields.Float(
        string='Quantidade SVL',
        compute='_compute_svl_values',
        digits='Product Unit of Measure',
    )
    value_svl = fields.Float(
        string='Valor SVL',
        compute='_compute_svl_values',
        digits='Product Price',
    )

    # Relação com SVL
    stock_valuation_layer_ids = fields.One2many(
        'stock.valuation.layer',
        'lot_group_id',
        string='Camadas de Valorização',
        readonly=True,
    )

    # Relação com anos fiscais PCMP
    pcmp_fiscal_year_ids = fields.One2many(
        'mh.pcmp.fiscal.year',
        'lot_group_id',
        string='PCMP por Ano Fiscal',
    )

    # ========================================
    # PREÇOS E MARGEM
    # ========================================

    manual_sale_price = fields.Boolean(
        string='Preço de Venda Manual',
        default=False,
        tracking=True,
        help='Se True, permite definir preço de venda manualmente em vez de calcular via PCMP × margem'
    )

    list_price = fields.Float(
        string='Preço de Venda Padrão',
        compute='_compute_list_price',
        store=True,
        digits='Product Price',
        tracking=True,
        help='Preço de venda calculado: custo × (1 + margin/100)'
    )

    manual_pcmp = fields.Float(
        string='PCMP Manual',
        digits='Product Price',
        tracking=True,
        help='PCMP manual (custo por m²/m³) usado quando manual_sale_price=True. '
             'O preço de venda é calculado: manual_pcmp × (1 + margin/100)'
    )

    # standard_price = custo médio calculado das SVL (antes era avg_cost)
    # SEM tracking — campo computed (val/qty das SVLs). Cada venda altera o
    # valor stored (precisão total), e tracking faria parecer que o vendedor
    # alterou o standard_price. Audit trail real está nos SVLs.
    standard_price = fields.Float(
        string='Custo Médio (SVL)',
        compute='_compute_standard_price',
        store=True,
        min_display_digits='Product Price',
        help='Custo médio calculado das camadas de valorização (value_svl / quantity_svl). '
             'Armazenado com precisão total (Odoo 18 standard pattern).'
    )

    # pcmp = PCMP por m²/m³ (computed via fórmula fiscal)
    # SEM tracking — campo computed. Mesma razão que standard_price acima.
    pcmp = fields.Float(
        string='PCMP',
        compute='_compute_pcmp',
        store=True,
        min_display_digits='Product Price',
        help='Preço de Custo Médio Ponderado calculado das SVLs do ano fiscal. '
             'Armazenado com precisão total; exibido com mín. 2 decimais. '
             'Audit trail está nas SVLs (stock.valuation.layer.create_uid).'
    )

    margin = fields.Float(
        string='Margem Padrão (%)',
        tracking=True,
        help='Margem de lucro padrão aplicada a todos os grupos de dimensões associados'
    )

    # ========================================
    # GRUPOS DE DIMENSÕES (lot.price.group)
    # ========================================

    lot_price_group_ids = fields.One2many(
        'lot.price.group',
        'base_lot_group_id',
        string='Grupos de Dimensões',
        readonly=True,
    )

    lot_price_group_count = fields.Integer(
        string='Nº de Grupos de Dimensões',
        compute='_compute_lot_price_group_count',
        store=True,
        help='Quantidade de grupos de dimensões associados a este grupo base'
    )

    # ========================================
    # CAMPOS INFORMATIVOS
    # ========================================

    total_quantity = fields.Float(
        string='Quantidade Total',
        compute='_compute_totals',
        digits='Product Unit of Measure',
        help='Soma das quantidades disponíveis de todos os grupos de dimensões'
    )

    total_value = fields.Float(
        string='Valor Total',
        compute='_compute_totals',
        digits='Product Price',
        help='Valor total em estoque (quantidade × preço de venda)'
    )

    # ========================================
    # CONSTRAINTS
    # ========================================

    _sql_constraints = [
        ('base_lot_name_product_company_uniq',
         'UNIQUE(base_lot_name, product_id, company_id)',
         'Já existe um grupo com este nome base para este produto nesta empresa!')
    ]

    @api.constrains('pcmp', 'list_price')
    def _check_prices_positive(self):
        """Validar que preços não sejam negativos"""
        for group in self:
            if group.pcmp < 0:
                raise ValidationError(
                    f"PCMP não pode ser negativo no grupo base '{group.name}'!\n\n"
                    f"Valor atual: {group.pcmp:.2f}\n\n"
                    f"Verifique o cálculo de PCMP."
                )
            if group.list_price < 0:
                raise ValidationError(
                    f"Preço de venda não pode ser negativo no grupo base '{group.name}'!\n\n"
                    f"Valor atual: {group.list_price:.2f}\n\n"
                    f"Verifique a margem e o cálculo de preço."
                )

    @api.constrains('manual_sale_price', 'manual_pcmp')
    def _check_manual_pricing_consistency(self):
        """Validar que PCMP manual esteja preenchido quando modo manual ativo"""
        for group in self:
            if group.manual_sale_price and (not group.manual_pcmp or group.manual_pcmp <= 0):
                raise ValidationError(
                    f"PCMP Manual obrigatório!\n\n"
                    f"Grupo: {group.name}\n\n"
                    f"Quando 'Preço de Venda Manual' está ativo, "
                    f"o campo 'PCMP Manual' deve ser preenchido com um valor maior que zero."
                )

    # ========================================
    # COMPUTED FIELDS
    # ========================================

    @api.depends('base_lot_name')
    def _compute_name(self):
        """Gera nome descritivo baseado em nome base do lote"""
        for group in self:
            base_name = group.base_lot_name or 'SEM-NOME'
            group.name = f"{base_name}"

    @api.depends('base_lot_name', 'product_id')
    def _compute_display_name(self):
        for record in self:
            if record.base_lot_name and record.product_id:
                record.display_name = f"{record.base_lot_name} ({record.product_id.display_name})"
            else:
                record.display_name = record.base_lot_name or _("Novo")

    @api.depends('stock_valuation_layer_ids.quantity', 'stock_valuation_layer_ids.value')
    def _compute_svl_values(self):
        """Calcula quantity_svl e value_svl das SVL do grupo."""
        for record in self:
            if not record.id:
                record.quantity_svl = 0.0
                record.value_svl = 0.0
                continue

            # Agregar valores das SVL
            svl_data = self.env['stock.valuation.layer'].sudo().read_group(
                domain=[
                    ('lot_group_id', '=', record.id),
                    ('company_id', '=', record.company_id.id),
                ],
                fields=['quantity:sum', 'value:sum'],
                groupby=[],
            )

            if svl_data:
                record.quantity_svl = svl_data[0].get('quantity', 0.0) or 0.0
                record.value_svl = svl_data[0].get('value', 0.0) or 0.0
            else:
                record.quantity_svl = 0.0
                record.value_svl = 0.0

    @api.depends('stock_valuation_layer_ids.quantity', 'stock_valuation_layer_ids.value')
    def _compute_standard_price(self):
        """Calcula standard_price (custo médio) das SVL do grupo.
        Quando stock zera, mantém último custo conhecido.
        """
        for record in self:
            if not record.id:
                record.standard_price = 0.0
                continue

            # Agregar valores das SVL
            svl_data = self.env['stock.valuation.layer'].sudo().read_group(
                domain=[
                    ('lot_group_id', '=', record.id),
                    ('company_id', '=', record.company_id.id),
                ],
                fields=['quantity:sum', 'value:sum'],
                groupby=[],
            )

            qty = svl_data[0].get('quantity', 0.0) or 0.0 if svl_data else 0.0
            val = svl_data[0].get('value', 0.0) or 0.0 if svl_data else 0.0

            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            if not float_is_zero(qty, precision_digits=precision):
                record.standard_price = val / qty
            else:
                # Stock zerado - manter último custo conhecido da BD
                self.env.cr.execute(
                    "SELECT standard_price FROM base_lot_group WHERE id = %s", (record.id,)
                )
                result = self.env.cr.fetchone()
                record.standard_price = result[0] if result and result[0] else 0.0

    @api.depends('product_id.cost_method', 'product_id.standard_price',
                 'stock_valuation_layer_ids.quantity', 'stock_valuation_layer_ids.value',
                 'pcmp_fiscal_year_ids.initial_pcmp', 'pcmp_fiscal_year_ids.initial_stock')
    def _compute_pcmp(self):
        """Calcula PCMP usando a fórmula fiscal.

        Fórmula: pcmp = (valor_inicial + soma_valor_svls) / (qty_inicial + soma_qty_svls)

        Dependências:
        - stock_valuation_layer_ids: SVLs do grupo (entradas, saídas, landed costs)
        - pcmp_fiscal_year_ids: Valores iniciais do ano fiscal
        """
        for record in self:
            if not record.id:
                record.pcmp = 0.0
                continue

            if record.product_id.cost_method != 'pcmp':
                record.pcmp = record.product_id.standard_price
                continue

            old_val = record.pcmp or 0.0
            new_val = record._compute_pcmp_value()
            record.pcmp = new_val

            # AUDIT LOG: se a mudança é VISÍVEL no display (2 decimais),
            # postar mensagem autorada por SYSTEM (não pelo utilizador que
            # disparou o recompute). Não polui chatter com drifts invisíveis
            # do AVCO; preserva auditabilidade fiscal de mudanças relevantes.
            if abs(round(old_val, 2) - round(new_val, 2)) > 0.001:
                record._log_pcmp_change(old_val, new_val)

    def _log_pcmp_change(self, old_val, new_val):
        """Posta no chatter mensagem de audit (autorada por sistema) quando
        o PCMP muda no display a 2 decimais. Filtra mudanças invisíveis."""
        # Saltar em modos de instalação / migração / scripts custom
        if self.env.context.get('install_mode') or self.env.context.get('skip_pcmp_log'):
            return
        try:
            msg = Markup(
                '<i class="fa fa-calculator"/> <b>PCMP recalculado automaticamente</b>'
                '<br/>%(old)s &rarr; %(new)s'
                '<br/><small>Origem: recompute SVL pool / qty</small>'
            ) % {
                'old': f"{old_val:,.2f}",
                'new': f"{new_val:,.2f}",
            }
            partner_root = self.env.ref('base.partner_root', raise_if_not_found=False)
            self.sudo().message_post(
                body=msg,
                author_id=partner_root.id if partner_root else False,
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )
        except Exception as e:
            _logger.warning("Falha ao postar audit log de PCMP em %s: %s", self, e)

    @api.depends('lot_price_group_ids')
    def _compute_lot_price_group_count(self):
        """Conta número de grupos de dimensões associados"""
        for group in self:
            group.lot_price_group_count = len(group.lot_price_group_ids)

    @api.depends('lot_price_group_ids.total_quantity', 'lot_price_group_ids.total_value')
    def _compute_totals(self):
        """Calcula quantidade total e valor total de todos os grupos de dimensões"""
        for group in self:
            group.total_quantity = sum(group.lot_price_group_ids.mapped('total_quantity'))
            group.total_value = sum(group.lot_price_group_ids.mapped('total_value'))


    @api.depends('pcmp', 'margin', 'manual_pcmp', 'manual_sale_price')
    def _compute_list_price(self):
        """Calcula list_price baseado no modo:
        - manual_sale_price=True: list_price = manual_pcmp × (1 + margin/100)
        - manual_sale_price=False: list_price = pcmp × (1 + margin/100)
        """
        for group in self:
            cost = group.manual_pcmp if group.manual_sale_price else group.pcmp
            if cost > 0 and group.margin:
                group.list_price = cost * (1 + group.margin / 100)
            elif cost > 0:
                group.list_price = cost
            else:
                group.list_price = 0.0

    # ========================================
    # MÉTODOS DE VALORIZAÇÃO PCMP
    # ========================================

    def _get_pcmp_fiscal_year_record(self, fiscal_year=None, company=None):
        """
        Obtém o registo PCMP para o ano fiscal especificado.

        :param fiscal_year: Ano fiscal (default: ano atual)
        :param company: Empresa (default: empresa atual)
        :return: recordset mh.pcmp.fiscal.year ou empty recordset
        """
        self.ensure_one()

        if not fiscal_year:
            fiscal_year = fields.Date.today().year

        if not company:
            company = self.env.company

        record = self.env['mh.pcmp.fiscal.year'].sudo().search([
            ('lot_group_id', '=', self.id),
            ('product_id', '=', self.product_id.id),
            ('fiscal_year', '=', fiscal_year),
            ('company_id', '=', company.id),
        ], limit=1)

        return record

    def _compute_pcmp_value(self, fiscal_year=None, company=None):
        """
        Calcula o PCMP usando a fórmula alinhada com Odoo standard_price.

        Fórmula (igual ao Odoo avg_cost):
            pcmp = (valor_inicial + soma_valor_svls) / (qty_inicial + soma_qty_svls)

        Soma TODAS as SVLs do lot_group_id sem filtros por tipo:
        - Entradas físicas (quantity > 0)
        - Saídas (quantity < 0)
        - Landed Costs (quantity = 0, value > 0)
        - Diferença de preço de fatura (quantity = 0, value +/-)

        :param fiscal_year: Ano fiscal (default: ano atual)
        :param company: Empresa (default: empresa atual)
        :return: Novo valor PCMP (float)
        """
        self.ensure_one()

        if not fiscal_year:
            fiscal_year = fields.Date.today().year

        if not company:
            company = self.env.company

        # Obter registo do ponto de partida (criado via transição de ano fiscal)
        pcmp_record = self._get_pcmp_fiscal_year_record(fiscal_year, company)

        # Valores do ponto de partida
        # Para grupos SEM registo: 0 (novos ou sem transição)
        # Para grupos COM registo: valores do registo de transição
        if pcmp_record:
            pcmp_initial = pcmp_record.initial_pcmp
            stock_initial = pcmp_record.initial_stock
        else:
            pcmp_initial = 0.0
            stock_initial = 0.0

        # Datas do ano fiscal
        date_from = f'{fiscal_year}-01-01'
        date_to = f'{fiscal_year}-12-31'

        # =====================================================================
        # NOVA LÓGICA: Alinhada com Odoo standard_price (avg_cost)
        # Soma TODAS as SVLs sem filtros por tipo - inclui automaticamente:
        # - Entradas (quantity > 0)
        # - Saídas (quantity < 0)
        # - Landed Costs (quantity = 0, value > 0)
        # - Diferença de preço de fatura (quantity = 0, value +/-)
        # =====================================================================
        all_svls = self.env['stock.valuation.layer'].sudo().search([
            ('lot_group_id', '=', self.id),
            ('product_id', '=', self.product_id.id),
            ('company_id', '=', company.id),
            ('create_date', '>=', date_from),
            ('create_date', '<=', date_to),
        ])
        total_quantity = sum(all_svls.mapped('quantity'))
        total_value = sum(all_svls.mapped('value'))

        # Fórmula PCMP (alinhada com Odoo)
        # pcmp = (valor_inicial + valor_svls) / (qty_inicial + qty_svls)
        numerator = (pcmp_initial * stock_initial) + total_value
        denominator = stock_initial + total_quantity

        # =====================================================================
        # CÓDIGO ANTERIOR (comentado para referência)
        # =====================================================================
        # # Buscar SVL de ENTRADA do ano fiscal (compras) - filtradas por lot_group_id
        # # NOTA: quantity > 0 são entradas físicas
        # in_svls = self.env['stock.valuation.layer'].search([
        #     ('lot_group_id', '=', self.id),
        #     ('product_id', '=', self.product_id.id),
        #     ('company_id', '=', company.id),
        #     ('create_date', '>=', date_from),
        #     ('create_date', '<=', date_to),
        #     ('quantity', '>', 0),  # Entradas físicas têm quantidade positiva
        # ])
        # import_qty = sum(in_svls.mapped('quantity'))
        # import_value = sum(in_svls.mapped('value'))
        #
        # # Buscar SVL de ajustes de Landed Costs (quantity = 0, value > 0)
        # # Estes ajustes aumentam o valor sem alterar a quantidade
        # landed_cost_svls = self.env['stock.valuation.layer'].search([
        #     ('lot_group_id', '=', self.id),
        #     ('product_id', '=', self.product_id.id),
        #     ('company_id', '=', company.id),
        #     ('create_date', '>=', date_from),
        #     ('create_date', '<=', date_to),
        #     ('quantity', '=', 0),  # Ajustes não alteram quantidade
        #     ('value', '>', 0),  # Mas aumentam o valor
        #     ('stock_landed_cost_id', '!=', False),  # Vêm de landed costs
        # ])
        # # Adicionar valor dos landed costs ao import_value (qty já está correcta)
        # import_value += sum(landed_cost_svls.mapped('value'))
        #
        # # Buscar SVL de SAÍDA do ano fiscal (vendas) - filtradas por lot_group_id
        # out_svls = self.env['stock.valuation.layer'].search([
        #     ('lot_group_id', '=', self.id),
        #     ('product_id', '=', self.product_id.id),
        #     ('company_id', '=', company.id),
        #     ('create_date', '>=', date_from),
        #     ('create_date', '<=', date_to),
        #     ('quantity', '<', 0),  # Saídas têm quantidade negativa
        # ])
        # sales_qty = abs(sum(out_svls.mapped('quantity')))
        # sales_value = abs(sum(out_svls.mapped('value')))
        #
        # # Fórmula PCMP (antiga)
        # numerator = (pcmp_initial * stock_initial) - sales_value + import_value
        # denominator = stock_initial - sales_qty + import_qty
        # =====================================================================

        precision = self.env['decimal.precision'].precision_get('Product Price')

        if float_is_zero(denominator, precision_digits=precision) or denominator < 0:
            # Stock zerado ou negativo - manter último PCMP conhecido
            # Ler da BD antes do recompute sobrescrever com 0
            if self.id:
                self.env.cr.execute(
                    "SELECT pcmp FROM base_lot_group WHERE id = %s", (self.id,)
                )
                result = self.env.cr.fetchone()
                if result and result[0]:
                    new_pcmp = result[0]
                else:
                    new_pcmp = pcmp_initial
            else:
                new_pcmp = pcmp_initial
        else:
            new_pcmp = numerator / denominator

        return new_pcmp

    # ========================================
    # MÉTODOS DE PRICING
    # ========================================

    def _inverse_list_price_with_margin(self):
        """Recalcula margem quando preço é alterado manualmente

        Usa o custo correcto conforme o modo:
        - manual_sale_price=False: usa pcmp
        - manual_sale_price=True: usa manual_pcmp
        """
        for group in self:
            # Determinar custo base conforme o modo
            cost = group.manual_pcmp if group.manual_sale_price else group.pcmp

            if group.margin > 0:  # SÓ recalcula se margem já está definida
                if group.list_price and cost and cost > 0:
                    # Margem = [(Preço - Custo) / Custo] × 100
                    group.margin = ((group.list_price - cost) / cost) * 100

    def write(self, vals):
        """Override write para recalcular margem e registar alterações

        NOTA: pcmp e margin são propagados automaticamente para lot.price.group
        via campos related e computed. Não é necessária propagação manual.
        """
        # Guardar valores originais para logging
        original_values = {}
        if 'list_price' in vals or 'pcmp' in vals or 'margin' in vals:
            for group in self:
                original_values[group.id] = {
                    'list_price': group.list_price,
                    'pcmp': group.pcmp,
                    'margin': group.margin,
                }

        result = super().write(vals)

        # Recalcular margem se preço foi alterado e margem já existe
        if 'list_price' in vals or 'pcmp' in vals:
            for group in self:
                group._inverse_list_price_with_margin()

        # Log no chatter se contexto apropriado
        if 'list_price' in vals or 'pcmp' in vals or 'margin' in vals:
            if self.env.context.get('log_propagation') or self.env.context.get('origin_document'):
                for group in self:
                    if group.id in original_values:
                        origin = self.env.context.get('origin_document', 'Atualização manual')
                        price_groups_count = len(group.lot_price_group_ids.filtered(lambda pg: pg.use_base_pricing))

                        changes = []
                        if 'pcmp' in vals:
                            old_val = original_values[group.id]['pcmp']
                            changes.append(f"PCMP: {old_val:.2f} → {group.pcmp:.2f} MT/m²")
                        if 'list_price' in vals:
                            old_val = original_values[group.id]['list_price']
                            changes.append(f"Venda: {old_val:.2f} → {group.list_price:.2f} MT/m²")
                        if 'margin' in vals:
                            old_val = original_values[group.id]['margin']
                            changes.append(f"Margem: {old_val:.2f}% → {group.margin:.2f}%")

                        if changes:
                            group.message_post(
                                body=f"<b>Preços atualizados</b><br/>"
                                     f"Origem: {origin}<br/>"
                                     f"Alterações: {', '.join(changes)}<br/>"
                                     f"Sincronizado com <b>{price_groups_count}</b> grupos de dimensões"
                            )

        return result

    # ========================================
    # AÇÕES (BOTÕES)
    # ========================================

    def action_view_stock_valuation_layers(self):
        """Ação para ver as camadas de valorização deste grupo."""
        self.ensure_one()
        return {
            'name': _('Camadas de Valorização'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.valuation.layer',
            'view_mode': 'list,form',
            'domain': [('lot_group_id', '=', self.id)],
            'context': {'default_lot_group_id': self.id},
        }

    def action_view_pcmp_fiscal_years(self):
        """Ação para ver os registos PCMP por ano fiscal deste grupo."""
        self.ensure_one()
        return {
            'name': _('PCMP por Ano Fiscal'),
            'type': 'ir.actions.act_window',
            'res_model': 'mh.pcmp.fiscal.year',
            'view_mode': 'list,form',
            'domain': [('lot_group_id', '=', self.id)],
            'context': {
                'default_lot_group_id': self.id,
                'default_product_id': self.product_id.id,
            },
        }

    def action_recalculate_pcmp(self):
        """Ação para forçar recálculo do PCMP do grupo.

        O PCMP é agora um campo computed. Esta ação invalida o cache
        e força o recálculo.
        """
        self.ensure_one()
        # Invalidar cache e forçar recálculo
        self.invalidate_recordset(['pcmp'])
        self.modified(['stock_valuation_layer_ids'])
        # Aceder ao campo para forçar recálculo
        new_pcmp = self.pcmp
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('PCMP Recalculado'),
                'message': _('O PCMP do grupo foi atualizado para: %.2f') % new_pcmp,
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def action_view_price_groups(self):
        """Ação para abrir lista de grupos de dimensões associados"""
        self.ensure_one()
        return {
            'name': f'Grupos de Dimensões - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'lot.price.group',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.lot_price_group_ids.ids)],
            'context': {'default_base_lot_group_id': self.id}
        }
