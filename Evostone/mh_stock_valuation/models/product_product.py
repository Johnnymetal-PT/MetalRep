# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools import float_is_zero
import logging

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # Campo para armazenar o nome antigo (antes da reestruturação)
    nome_antigo = fields.Char(
        string='Nome Antigo',
        help='Nome original do produto antes da reestruturação de variantes',
    )

    # Relação com SVLs do produto (para computed pcmp)
    stock_valuation_layer_ids = fields.One2many(
        'stock.valuation.layer',
        'product_id',
        string='Camadas de Valorização',
        domain=[('lot_group_id', '=', False)],  # Apenas SVLs a nível de produto
    )

    # Relação com registos PCMP por ano fiscal
    pcmp_fiscal_year_ids = fields.One2many(
        'mh.pcmp.fiscal.year',
        'product_id',
        string='PCMP por Ano Fiscal',
    )
    
    # Redefinir campo pcmp com compute (campo base definido em mh_inventory)
    # min_display_digits (Odoo 18 standard) = storage com precisão total,
    # exibição com mín. 2 decimais. Resolve drift de arredondamento AVCO.
    pcmp = fields.Float(
        compute='_compute_pcmp_from_svl',
        store=True,
        min_display_digits='Product Price',
    )

    # Relação com grupos de dimensões (lot.price.group)
    lot_price_group_ids = fields.One2many(
        'lot.price.group',
        'product_id',
        string='Grupos de Dimensões',
    )

    lot_price_group_count = fields.Integer(
        string='Nº Grupos de Dimensões',
        compute='_compute_lot_price_group_count',
    )

    # Relação com grupos de lotes (base.lot.group)
    base_lot_group_ids = fields.One2many(
        'base.lot.group',
        'product_id',
        string='Grupos de Lotes',
    )

    base_lot_group_count = fields.Integer(
        string='Nº Grupos de Lotes',
        compute='_compute_base_lot_group_count',
    )

    @api.depends('lot_price_group_ids')
    def _compute_lot_price_group_count(self):
        # Este contador esta na ficha do produto e e' calculado em cada
        # leitura. Percorrer o One2many exige acesso a lot.price.group, que so
        # o gestor de armazem tem. Sem esta guarda, ninguem mais consegue abrir
        # a ficha de um produto — nem vendedor, nem compras, nem contabilidade.
        if not self.env['lot.price.group'].has_access('read'):
            for product in self:
                product.lot_price_group_count = 0
            return
        for product in self:
            product.lot_price_group_count = len(product.lot_price_group_ids)

    @api.depends('base_lot_group_ids')
    def _compute_base_lot_group_count(self):
        # Ver a nota em _compute_lot_price_group_count: mesmo efeito, para
        # base.lot.group.
        if not self.env['base.lot.group'].has_access('read'):
            for product in self:
                product.base_lot_group_count = 0
            return
        for product in self:
            product.base_lot_group_count = len(product.base_lot_group_ids)

    @api.depends('cost_method', 'standard_price',
                 'stock_valuation_layer_ids.quantity', 'stock_valuation_layer_ids.value',
                 'pcmp_fiscal_year_ids.initial_pcmp', 'pcmp_fiscal_year_ids.initial_stock')
    def _compute_pcmp_from_svl(self):
        """Calcula PCMP usando a fórmula fiscal.

        Fórmula: pcmp = (valor_inicial + soma_valor_svls) / (qty_inicial + soma_qty_svls)

        Dependências:
        - stock_valuation_layer_ids: SVLs do produto (apenas lot_group_id=False)
        - pcmp_fiscal_year_ids: Valores iniciais do ano fiscal
        """
        for product in self:
            if not product.id:
                product.pcmp = 0.0
                continue

            if product.cost_method != 'pcmp':
                product.pcmp = product.standard_price
                continue

            # Usar o método existente que já tem toda a lógica
            result = product._compute_pcmp()
            _logger.info(
                f"📌 _compute_pcmp_from_svl [{product.default_code}] id={product.id}: "
                f"result={result} type={type(result).__name__}"
            )
            product.pcmp = result

    def _get_pcmp_fiscal_year_record(self, fiscal_year=None, company=None):
        """
        Obtém o registo PCMP para o ano fiscal especificado (nível produto).

        :param fiscal_year: Ano fiscal (default: ano atual)
        :param company: Empresa (default: empresa atual)
        :return: recordset mh.pcmp.fiscal.year ou empty recordset
        """
        self.ensure_one()

        if not fiscal_year:
            fiscal_year = fields.Date.today().year

        if not company:
            company = self.env.company

        # Buscar registo SEM lot_group_id (nível produto)
        record = self.env['mh.pcmp.fiscal.year'].sudo().search([
            ('product_id', '=', self.id),
            ('fiscal_year', '=', fiscal_year),
            ('company_id', '=', company.id),
            ('lot_group_id', '=', False),  # Apenas nível produto
        ], limit=1)

        return record

    def _get_pcmp_initial_values(self, fiscal_year=None, company=None):
        """
        Retorna os valores do ponto de partida do ano fiscal.

        :param fiscal_year: Ano fiscal (default: ano atual)
        :param company: Empresa (default: empresa atual)
        :return: dict com 'stock', 'pcmp', 'value'
        """
        self.ensure_one()

        record = self._get_pcmp_fiscal_year_record(fiscal_year, company)

        if record:
            return {
                'stock': record.initial_stock,
                'pcmp': record.initial_pcmp,
                'value': record.initial_value,
            }

        return {
            'stock': 0.0,
            'pcmp': 0.0,
            'value': 0.0,
        }

    def _compute_pcmp(self, fiscal_year=None, company=None):
        """
        Calcula o PCMP usando a fórmula alinhada com Odoo standard_price.

        Fórmula (igual ao base.lot.group):
            pcmp = (valor_inicial + soma_valor_svls) / (qty_inicial + soma_qty_svls)

        Soma TODAS as SVLs do produto sem filtros por tipo:
        - Entradas físicas (quantity > 0)
        - Saídas (quantity < 0)
        - Landed Costs (quantity = 0, value > 0)
        - Diferença de preço de fatura (quantity = 0, value +/-)

        :param fiscal_year: Ano fiscal (default: ano atual)
        :param company: Empresa (default: empresa atual)
        :return: Novo valor PCMP (float)
        """
        self.ensure_one()
        _logger.info(f"📌 _compute_pcmp START [{self.default_code}] id={self.id}")

        if not fiscal_year:
            fiscal_year = fields.Date.today().year

        if not company:
            company = self.env.company

        # Obter registo do ponto de partida (criado via transição de ano fiscal)
        pcmp_record = self._get_pcmp_fiscal_year_record(fiscal_year, company)

        # Valores do ponto de partida
        # Para produtos SEM registo: 0 (produtos novos ou sem transição)
        # Para produtos COM registo: valores do registo de transição
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
        # LÓGICA ALINHADA COM base.lot.group:
        # Soma TODAS as SVLs sem filtros por tipo - inclui automaticamente:
        # - Entradas (quantity > 0)
        # - Saídas (quantity < 0)
        # - Landed Costs (quantity = 0, value > 0)
        # - Diferença de preço de fatura (quantity = 0, value +/-)
        # =====================================================================
        all_svls = self.env['stock.valuation.layer'].sudo().search([
            ('product_id', '=', self.id),
            ('company_id', '=', company.id),
            ('create_date', '>=', date_from),
            ('create_date', '<=', date_to),
            ('lot_group_id', '=', False),  # Apenas nível produto
        ])
        total_quantity = sum(all_svls.mapped('quantity'))
        total_value = sum(all_svls.mapped('value'))

        # Fórmula PCMP (alinhada com Odoo e base.lot.group)
        # pcmp = (valor_inicial + valor_svls) / (qty_inicial + qty_svls)
        numerator = (pcmp_initial * stock_initial) + total_value
        denominator = stock_initial + total_quantity

        precision = self.env['decimal.precision'].precision_get('Product Price')

        if float_is_zero(denominator, precision_digits=precision) or denominator < 0:
            # Stock zerado ou negativo - manter último PCMP conhecido
            if self.id:
                self.env.cr.execute(
                    "SELECT pcmp FROM product_product WHERE id = %s", (self.id,)
                )
                result = self.env.cr.fetchone()
                if result and result[0] and isinstance(result[0], (int, float)):
                    new_pcmp = result[0]
                else:
                    new_pcmp = pcmp_initial
            else:
                new_pcmp = pcmp_initial
        else:
            new_pcmp = numerator / denominator

        _logger.info(
            f"📌 _compute_pcmp END [{self.default_code}] id={self.id}: "
            f"new_pcmp={new_pcmp} type={type(new_pcmp).__name__} "
            f"denominator={denominator} numerator={numerator}"
        )
        return new_pcmp

    def _get_pcmp_moves(self, move_type, date_from, date_to, company):
        """
        Obtém os movimentos de stock para cálculo do PCMP.

        :param move_type: 'in' para entradas, 'out' para saídas
        :param date_from: Data início (string 'YYYY-MM-DD')
        :param date_to: Data fim (string 'YYYY-MM-DD')
        :param company: Empresa
        :return: recordset stock.move
        """
        self.ensure_one()

        StockMove = self.env['stock.move']

        domain = [
            ('product_id', '=', self.id),
            ('state', '=', 'done'),
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('company_id', '=', company.id),
        ]

        if move_type == 'in':
            # Entradas: destino é localização interna, origem não é
            domain.extend([
                ('location_dest_id.usage', '=', 'internal'),
                ('location_id.usage', '!=', 'internal'),
            ])
        else:
            # Saídas: origem é localização interna, destino não é
            domain.extend([
                ('location_id.usage', '=', 'internal'),
                ('location_dest_id.usage', '!=', 'internal'),
            ])

        return StockMove.search(domain)

    def _get_move_unit_cost(self, move):
        """
        Obtém o custo unitário de um movimento.

        :param move: stock.move record
        :return: float custo unitário
        """
        # Tentar obter preço do movimento
        if move.price_unit:
            return abs(move.price_unit)

        # Tentar obter das SVL associadas
        svl = move.stock_valuation_layer_ids.filtered(lambda l: l.quantity > 0)
        if svl:
            return abs(svl[0].unit_cost)

        # Fallback: usar standard_price do produto
        return self.with_company(move.company_id).standard_price

    def _prepare_out_svl_vals(self, quantity, company, lot=False, lot_group=False):
        """
        Override para usar pcmp quando cost_method == 'pcmp'.

        :param quantity: Quantidade a sair
        :param company: Empresa
        :param lot: stock.lot record (opcional)
        :param lot_group: base.lot.group record (opcional) - se definido, usa pcmp do grupo
        """
        if self.cost_method == 'pcmp':
            # Usar pcmp do lot_group (se definido) ou pcmp do produto
            if lot_group:
                cost = lot_group.pcmp or 0.0
            else:
                cost = self.with_company(company).pcmp or 0.0

            currency = company.currency_id
            value = currency.round(cost * quantity)

            vals = {
                'product_id': self.id,
                'value': -value,  # Negativo para saídas
                'unit_cost': cost,
                'quantity': -quantity,  # Negativo para saídas
            }

            # Executar FIFO para tracking (mesmo comportamento que AVCO)
            # mas não usar os valores de FIFO para PCMP
            fifo_vals = self._run_fifo(abs(quantity), company, lot=lot)
            vals['remaining_qty'] = fifo_vals.get('remaining_qty', 0)

            return vals

        return super()._prepare_out_svl_vals(quantity, company, lot=lot)

    def _prepare_in_svl_vals(self, quantity, unit_cost, lot=False):
        """
        Override para garantir consistência quando cost_method == 'pcmp'.
        """
        if self.cost_method == 'pcmp':
            # Para PCMP, o unit_cost da entrada é o preço da compra
            # (não o PCMP calculado)
            company_id = self.env.context.get('force_company', self.env.company.id)
            company = self.env['res.company'].browse(company_id)
            value = company.currency_id.round(unit_cost * quantity)

            return {
                'product_id': self.id,
                'value': value,
                'unit_cost': unit_cost,
                'quantity': quantity,
                'remaining_qty': quantity,
                'remaining_value': value,
                'company_id': company_id,
                'lot_id': lot.id if lot else False,
            }

        return super()._prepare_in_svl_vals(quantity, unit_cost, lot=lot)

    def action_view_pcmp_fiscal_years(self):
        """Ação para ver os registos PCMP por ano fiscal deste produto."""
        self.ensure_one()
        return {
            'name': _('PCMP por Ano Fiscal'),
            'type': 'ir.actions.act_window',
            'res_model': 'mh.pcmp.fiscal.year',
            'view_mode': 'tree,form',
            'domain': [('product_id', '=', self.id)],
            'context': {'default_product_id': self.id},
        }

    def action_view_dimension_groups(self):
        """Ação para ver os grupos de dimensões (lot.price.group) deste produto."""
        self.ensure_one()
        return {
            'name': _('Grupos de Dimensões'),
            'type': 'ir.actions.act_window',
            'res_model': 'lot.price.group',
            'view_mode': 'list,form',
            'domain': [('product_id', '=', self.id)],
            'context': {
                'default_product_id': self.id,
                'search_default_product_id': self.id,
            },
        }

    def action_view_lot_groups(self):
        """Ação para ver os grupos de lotes (base.lot.group) deste produto."""
        self.ensure_one()
        return {
            'name': _('Grupos de Lotes'),
            'type': 'ir.actions.act_window',
            'res_model': 'base.lot.group',
            'view_mode': 'list,form',
            'domain': [('product_id', '=', self.id)],
            'context': {
                'default_product_id': self.id,
                'search_default_product_id': self.id,
            },
        }
