# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from collections import defaultdict
import logging

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = 'stock.move'

    lot_group_id = fields.Many2one(
        'base.lot.group',
        string='Grupo de Lote',
        index=True,
        help="Grupo de lote para valorização PCMP.",
    )

    snapshot_ids = fields.One2many(
        'stock.move.line.snapshot',
        'move_id',
        string='Snapshots Pré-Split',
        help='Estado das move_lines antes do split por units_qty na validação do picking.',
    )

    def action_open_snapshots(self):
        """Abre lista com os snapshots pré-split deste movimento."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Snapshots Pré-Split — %s', self.product_id.display_name),
            'res_model': 'stock.move.line.snapshot',
            'view_mode': 'list,form',
            'domain': [('move_id', '=', self.id)],
            'target': 'new',
            'context': {'default_move_id': self.id},
        }

    # ========================================
    # MÉTODOS AUXILIARES PARA DEVOLUÇÕES
    # ========================================

    def _is_return(self):
        """
        Verifica se o movimento é uma devolução.

        Alinhado com Odoo 18 - usa dois critérios:
        1. origin_returned_move_id preenchido (referência ao move original)
        2. location.usage (customer para devolução de venda, supplier para devolução de compra)

        :return: True se for devolução, False caso contrário
        """
        self.ensure_one()
        # Método 1: Move tem referência ao move original devolvido (Odoo 18)
        if self.origin_returned_move_id:
            return True
        # Método 2: Verificar location.usage (Odoo 18 _is_returned)
        # Devolução de venda: origem é cliente (customer)
        if self.location_id and self.location_id.usage == 'customer':
            return True
        # Devolução de compra: destino é fornecedor (supplier)
        if self.location_dest_id and self.location_dest_id.usage == 'supplier':
            return True
        return False

    def _is_sale_return(self):
        """
        Verifica se é uma devolução de VENDA (cliente devolve).

        Alinhado com Odoo 18 _is_returned('in'):
        - location_id.usage == 'customer' (mercadoria vem do cliente)
        - OU origin_returned_move_id existe e é entrada

        :return: True se for devolução de venda
        """
        self.ensure_one()
        # Odoo 18: _is_returned('in') = location_id.usage == 'customer'
        if self.location_id and self.location_id.usage == 'customer':
            return True
        # Fallback: origin_returned_move_id + é entrada
        if self.origin_returned_move_id and self._is_in():
            return True
        return False

    def _is_purchase_return(self):
        """
        Verifica se é uma devolução de COMPRA (devolver ao fornecedor).

        Alinhado com Odoo 18 _is_returned('out'):
        - location_dest_id.usage == 'supplier' (mercadoria vai para fornecedor)
        - OU origin_returned_move_id existe e é saída

        :return: True se for devolução de compra
        """
        self.ensure_one()
        # Odoo 18: _is_returned('out') = location_dest_id.usage == 'supplier'
        if self.location_dest_id and self.location_dest_id.usage == 'supplier':
            return True
        # Fallback: origin_returned_move_id + é saída
        if self.origin_returned_move_id and self._is_out():
            return True
        return False

    def _get_return_fallback_cost(self):
        """
        Obtém custo de fallback para devoluções quando não há SVL original.

        Prioridade:
        1. PCMP do lot_group (se existir)
        2. PCMP do produto
        3. standard_price do produto

        :return: float custo unitário
        """
        self.ensure_one()

        # 1. PCMP do lot_group
        if self.lot_group_id and self.lot_group_id.pcmp:
            _logger.info(
                f"Devolução fallback: Move {self.id} usa PCMP do lot_group = {self.lot_group_id.pcmp}"
            )
            return self.lot_group_id.pcmp

        # 2. PCMP do produto
        pcmp = self.product_id.with_company(self.company_id).pcmp
        if pcmp:
            _logger.info(
                f"Devolução fallback: Move {self.id} usa PCMP do produto = {pcmp}"
            )
            return pcmp

        # 3. standard_price do produto
        std_price = self.product_id.with_company(self.company_id).standard_price
        _logger.info(
            f"Devolução fallback: Move {self.id} usa standard_price = {std_price}"
        )
        return std_price

    def _action_done(self, cancel_backorder=False):
        """
        Override para calcular PCMP após SVLs serem criadas.

        Sequência:
        1. super()._action_done() → chama product_price_update_before_done() e cria SVLs
        2. _pcmp_price_update_after_done() → calcula PCMP com SVLs já criadas
        """
        # Chamar super() que:
        # - Chama product_price_update_before_done() (prepara lot_groups)
        # - Cria SVLs com _create_in_svl() e _create_out_svl()
        res = super()._action_done(cancel_backorder=cancel_backorder)

        # Agora as SVLs existem - calcular PCMP
        self._pcmp_price_update_after_done()

        return res

    def _get_or_create_lot_group(self):
        """
        Obtém ou cria o grupo de lote baseado no lot_name.

        Ao criar um novo grupo, inicializa pcmp e standard_price
        com o price_unit do movimento (custo de entrada).

        :return: base.lot.group record ou False
        """
        self.ensure_one()
        if not self.lot_name:
            return False

        LotGroup = self.env['base.lot.group'].sudo()

        # Buscar grupo existente por base_lot_name
        lot_group = LotGroup.search([
            ('base_lot_name', '=', self.lot_name),
            ('product_id', '=', self.product_id.id),
            ('company_id', '=', self.company_id.id),
        ], limit=1)

        if not lot_group:
            # Obter custo unitário do movimento
            unit_cost = self.price_unit or self.product_id.standard_price

            # Criar novo grupo COM valores iniciais (sudo para garantir permissões)
            lot_group = LotGroup.sudo().create({
                'base_lot_name': self.lot_name,
                'product_id': self.product_id.id,
                'company_id': self.company_id.id,
                'pcmp': unit_cost,
            })

        return lot_group

    def product_price_update_before_done(self, forced_qty=None):
        """
        Override para processar PCMP em movimentos de entrada.

        Este método é chamado em _action_done() ANTES de criar as SVL.
        Para PCMP, apenas preparamos os lot_groups aqui.
        O cálculo do PCMP é feito DEPOIS das SVLs serem criadas.

        IMPORTANTE: Devoluções de venda NÃO criam novos lot_groups.
        O lot_group é obtido do movimento original devolvido.
        """
        # Chamar super() para processar AVCO e outros métodos normalmente
        super().product_price_update_before_done(forced_qty=forced_qty)

        # Preparar lot_groups para movimentos PCMP (mas não calcular PCMP ainda)
        # EXCLUIR DEVOLUÇÕES - não criam novos lot_groups
        pcmp_moves = self.filtered(
            lambda m: m._is_in() and
            m.product_id.cost_method == 'pcmp' and
            m.product_id.is_storable and
            not m._is_return()  # EXCLUIR DEVOLUÇÕES
        )

        for move in pcmp_moves:
            # Só criar lot_group se:
            # - lot_name definido e diferente de 'SEM-LOTE'
            # - product_form != 'none' (produtos com forma física)
            product_form = getattr(move.product_id, 'product_form', 'none')
            has_valid_lot = move.lot_name and move.lot_name != 'SEM-LOTE'
            if has_valid_lot and product_form != 'none':
                # Obter ou criar grupo de lote
                lot_group = move._get_or_create_lot_group()
                if lot_group:
                    move.lot_group_id = lot_group.id

        # Para DEVOLUÇÕES DE VENDA: obter lot_group do movimento original
        return_moves = self.filtered(
            lambda m: m._is_in() and
            m.product_id.cost_method == 'pcmp' and
            m.product_id.is_storable and
            m._is_return()
        )

        for move in return_moves:
            # Obter lot_group do movimento original devolvido
            if move.origin_returned_move_id and move.origin_returned_move_id.lot_group_id:
                move.lot_group_id = move.origin_returned_move_id.lot_group_id.id
                _logger.info(
                    f"Devolução de venda: Move {move.id} herda lot_group_id={move.lot_group_id.id} "
                    f"do move original {move.origin_returned_move_id.id}"
                )

    def _pcmp_price_update_after_done(self):
        """
        Atualiza o PCMP DEPOIS das SVLs serem criadas.

        Este método é chamado em _action_done() após _create_in_svl().
        Agora as SVLs existem e podemos calcular o PCMP correctamente.

        NOTA: Alinhado com Odoo 18 AVCO - recalcula PCMP mesmo em devoluções.
        Como a devolução usa o preço das SVL originais, o impacto no PCMP é mínimo.
        """
        # Recalcular PCMP para TODAS as entradas (incluindo devoluções - Odoo 18)
        pcmp_moves = self.filtered(
            lambda m: m._is_in() and
            m.product_id.cost_method == 'pcmp' and
            m.product_id.is_storable
        )

        if not pcmp_moves:
            return

        for move in pcmp_moves:
            company = move.company_id
            move_date = move.date.date() if hasattr(move.date, 'date') else move.date
            fiscal_year = move_date.year

            # PCMP é agora um campo computed - sincroniza automaticamente com SVLs.
            # Forçar invalidação do cache para garantir recálculo.
            if move.lot_group_id:
                # Valorização por grupo de lote
                move.lot_group_id.invalidate_recordset(['pcmp'])
            else:
                # Valorização por produto
                move.product_id.invalidate_recordset(['pcmp'])

    def _get_pcmp_unit_cost(self, move):
        """
        Obtém o custo unitário para cálculo PCMP de um movimento.

        Prioridade:
        1. Se origem for PO: recalcula com taxa da data de validação (standard Odoo)
        2. price_unit do movimento (se definido)
        3. standard_price do produto

        :param move: stock.move record
        :return: float custo unitário
        """
        # 1. Compra: converter preço PO para moeda empresa com taxa da data de recepção
        if move.purchase_line_id:
            po_line = move.purchase_line_id
            order = po_line.order_id
            po_currency = order.currency_id
            company_currency = order.company_id.currency_id
            if po_currency == company_currency:
                return abs(move.price_unit)
            else:
                picking_date = move.picking_id.date_done or fields.Datetime.now()
                return abs(po_currency._convert(
                    po_line.price_unit, company_currency,
                    order.company_id, picking_date.date(), round=False
                ))

        # 2. Preço explícito no movimento (transferências, etc.)
        if move.price_unit:
            return abs(move.price_unit)

        # 3. Fallback: standard_price do produto
        return move.product_id.with_company(move.company_id).standard_price

    def _get_in_svl_vals(self, forced_quantity):
        """
        Override para incluir lógica PCMP na criação de SVL de entrada.

        `PORQUE E' QUE ISTO PERCORRE O CONJUNTO`
        O Odoo chama este método sobre **todos** os movimentos de uma vez
        (stock_account/models/stock_move.py::_create_in_svl). A versão anterior
        lia `self.product_id.cost_method` directamente, o que exige um registo
        único: com dois ou mais movimentos de produtos não-PCMP na mesma
        recepção rebentava com `Expected singleton: product.product(...)`.

        Não dava sinal enquanto a categoria «Mercadoria» esteve em PCMP, porque
        nesse caso o `_create_in_svl` já os separava e iterava um a um. Passou a
        dar quando a categoria mudou para custo médio.
        """
        # Para PCMP, precisamos garantir que o unit_cost seja o preço da compra
        # e não o PCMP calculado
        pcmp_moves = self.filtered(lambda m: m.product_id.cost_method == 'pcmp')
        other_moves = self - pcmp_moves

        svl_vals_list = []
        for move in pcmp_moves:
            svl_vals_list += move._get_pcmp_in_svl_vals(forced_quantity)
        if other_moves:
            svl_vals_list += super(StockMove, other_moves)._get_in_svl_vals(forced_quantity)

        return svl_vals_list

    def _get_pcmp_in_svl_vals(self, forced_quantity):
        """
        Prepara valores SVL de entrada para produtos com PCMP.

        Similar ao comportamento AVCO/Standard:
        - Se lot_valuated=True: cria SVL separado por lote
        - Se lot_valuated=False: agrega tudo numa única SVL

        IMPORTANTE para DEVOLUÇÕES DE VENDA:
        - Usa PCMP actual (do lot_group ou produto) em vez do price_unit
        - Isto garante que o valor da devolução seja consistente com o custo médio
        - O PCMP NÃO é recalculado (tratado em _pcmp_price_update_after_done)
        """
        self.ensure_one()
        svl_vals_list = []

        # Agregar quantidades por lote
        quantity_by_lot = defaultdict(float)
        if forced_quantity:
            quantity_by_lot[forced_quantity[0]] += forced_quantity[1]
        else:
            for move_line in self._get_in_move_lines():
                quantity_by_lot[move_line.lot_id] += move_line.quantity_product_uom

        # Obter custo unitário
        # Para DEVOLUÇÕES: usar preço das SVL originais (padrão Odoo 18)
        if self._is_return() and self.origin_returned_move_id:
            # Devolução: usar preço das SVL do movimento original (como Odoo 18 faz)
            original_svls = self.origin_returned_move_id.sudo().stock_valuation_layer_ids
            if original_svls:
                total_qty = sum(original_svls.mapped('quantity'))
                total_value = sum(original_svls.mapped('value'))
                if total_qty and abs(total_qty) > 0.0001:
                    unit_cost = abs(total_value / total_qty)
                    _logger.info(
                        f"Devolução: Move {self.id} usa preço original das SVL = {unit_cost}"
                    )
                else:
                    # Fallback: usar PCMP do lot_group ou produto
                    unit_cost = self._get_return_fallback_cost()
            else:
                # Sem SVL original: usar PCMP do lot_group ou produto
                unit_cost = self._get_return_fallback_cost()
        else:
            # Compra normal: usar preço da compra
            unit_cost = self._get_pcmp_unit_cost(self)

        # Verificar se produto tem valorização por lote
        if self.product_id.lot_valuated:
            # lot_valuated=True: criar SVL separado por lote
            for lot, qty in quantity_by_lot.items():
                vals = self.product_id._prepare_in_svl_vals(qty, unit_cost, lot)
                vals.update(self._prepare_common_svl_vals())

                # Obter lot_group: primeiro do movimento, depois do lote
                lot_group = self.lot_group_id or self._get_lot_group_for_lot(lot)
                if lot_group:
                    vals['lot_group_id'] = lot_group.id
                    _logger.info(
                        f"Entrada PCMP: lot={lot.name if lot else 'N/A'}, lot_group={lot_group.name}"
                    )

                if forced_quantity:
                    vals['description'] = (
                        vals.get('description', '') +
                        _("\nCorrection of %s (modification of past move)",
                          lot.display_name if lot else self.product_id.display_name)
                    )

                svl_vals_list.append(vals)
        else:
            # lot_valuated=False: agregar tudo numa única SVL
            total_qty = sum(quantity_by_lot.values())
            vals = self.product_id._prepare_in_svl_vals(total_qty, unit_cost)
            vals.update(self._prepare_common_svl_vals())

            # Obter lot_group: primeiro do movimento, depois dos lotes
            lot_group = self.lot_group_id
            if not lot_group:
                for lot in quantity_by_lot.keys():
                    lot_group = self._get_lot_group_for_lot(lot)
                    if lot_group:
                        break

            if lot_group:
                vals['lot_group_id'] = lot_group.id
                _logger.info(
                    f"Entrada PCMP (agregado): lot_group={lot_group.name}"
                )

            if forced_quantity:
                vals['description'] = (
                    vals.get('description', '') +
                    _("\nCorrection of %s (modification of past move)",
                      self.product_id.display_name)
                )

            svl_vals_list.append(vals)

        return svl_vals_list

    def _create_in_svl(self, forced_quantity=None):
        """
        Override para criar SVL de entrada para produtos PCMP.

        Este método é chamado em _action_done() para criar as camadas
        de valorização de entrada (stock.valuation.layer).
        """
        # Separar movimentos PCMP dos outros
        pcmp_moves = self.filtered(lambda m: m.product_id.cost_method == 'pcmp')
        other_moves = self - pcmp_moves

        svl = self.env['stock.valuation.layer']

        # Processar movimentos PCMP
        if pcmp_moves:
            svl_vals_list = []
            for move in pcmp_moves:
                svl_vals_list += move._get_in_svl_vals(forced_quantity)
            if svl_vals_list:
                svl |= self.env['stock.valuation.layer'].sudo().create(svl_vals_list)

        # Processar outros movimentos via super()
        if other_moves:
            svl |= super(StockMove, other_moves)._create_in_svl(forced_quantity)

        return svl

    def _create_out_svl(self, forced_quantity=None):
        """
        Override para criar SVL de saída para produtos PCMP.

        Este método é chamado em _action_done() para criar as camadas
        de valorização de saída (stock.valuation.layer).
        """
        # Separar movimentos PCMP dos outros
        pcmp_moves = self.filtered(lambda m: m.product_id.cost_method == 'pcmp')
        other_moves = self - pcmp_moves

        svl = self.env['stock.valuation.layer']

        # Processar movimentos PCMP
        if pcmp_moves:
            svl_vals_list = []
            for move in pcmp_moves:
                svl_vals_list += move._get_out_svl_vals(forced_quantity)
            if svl_vals_list:
                svl |= self.env['stock.valuation.layer'].sudo().create(svl_vals_list)

        # Processar outros movimentos via super()
        if other_moves:
            svl |= super(StockMove, other_moves)._create_out_svl(forced_quantity)

        return svl

    def _get_out_svl_vals(self, forced_quantity):
        """
        Override para incluir lógica PCMP na criação de SVL de saída.

        O mesmo defeito do `_get_in_svl_vals`, e pelo mesmo motivo: o Odoo chama
        isto sobre o conjunto dos movimentos. Aqui rebentaria numa expedição com
        mais do que uma linha de produto não-PCMP. Ainda não se tinha visto
        porque ainda não houve nenhuma saída.
        """
        pcmp_moves = self.filtered(lambda m: m.product_id.cost_method == 'pcmp')
        other_moves = self - pcmp_moves

        svl_vals_list = []
        for move in pcmp_moves:
            svl_vals_list += move._get_pcmp_out_svl_vals(forced_quantity)
        if other_moves:
            svl_vals_list += super(StockMove, other_moves)._get_out_svl_vals(forced_quantity)

        return svl_vals_list

    def _get_lot_group_for_lot(self, lot):
        """
        Obtém o base.lot.group para um dado stock.lot.

        Métodos de busca (por ordem de prioridade):
        1. lot.price_group_id.base_lot_group_id (via lot.price.group)
        2. Buscar por base_lot_name + product_id
        3. self.lot_group_id (fallback do movimento)

        :param lot: stock.lot record
        :return: base.lot.group record ou False
        """
        if not lot:
            return self.lot_group_id or False

        # Método 1: Via price_group_id
        if lot.sudo().price_group_id and lot.sudo().price_group_id.base_lot_group_id:
            return lot.sudo().price_group_id.base_lot_group_id

        # Método 2: Buscar por base_lot_name
        if lot.base_lot_name:
            lot_group = self.env['base.lot.group'].sudo().search([
                ('base_lot_name', '=', lot.base_lot_name),
                ('product_id', '=', self.product_id.id),
                ('company_id', '=', self.company_id.id),
            ], limit=1)
            if lot_group:
                return lot_group

        # Método 3: Fallback - lot_group_id do movimento
        return self.lot_group_id or False

    def _get_pcmp_out_svl_vals(self, forced_quantity):
        """
        Prepara valores SVL de saída para produtos com PCMP.

        Similar ao comportamento AVCO/Standard:
        - Se lot_valuated=True: cria SVL separado por lote
        - Se lot_valuated=False: agrega tudo numa única SVL

        Usa pcmp do lot_group (se definido) ou do produto para valorizar as saídas.
        """
        self.ensure_one()
        svl_vals_list = []

        # Agregar quantidades por lote
        quantity_by_lot = defaultdict(float)
        if forced_quantity:
            quantity_by_lot[forced_quantity[0]] += forced_quantity[1]
        else:
            for move_line in self._get_out_move_lines():
                quantity_by_lot[move_line.lot_id] += move_line.quantity_product_uom

        # Verificar se produto tem valorização por lote
        if self.product_id.lot_valuated:
            # lot_valuated=True: criar SVL separado por lote
            for lot, qty in quantity_by_lot.items():
                # Obter lot_group através do lote (NÃO do movimento!)
                lot_group = self._get_lot_group_for_lot(lot)

                if lot_group:
                    _logger.info(
                        f"Venda PCMP: lot={lot.name if lot else 'N/A'}, "
                        f"lot_group={lot_group.name}, pcmp={lot_group.pcmp}"
                    )
                    # Usar PCMP do grupo de lote
                    vals = self.product_id._prepare_out_svl_vals(
                        qty, self.company_id, lot=lot, lot_group=lot_group
                    )
                else:
                    # Usar PCMP do produto
                    vals = self.product_id._prepare_out_svl_vals(qty, self.company_id, lot=lot)

                vals.update(self._prepare_common_svl_vals())

                # Adicionar lot_group_id se definido
                if lot_group:
                    vals['lot_group_id'] = lot_group.id

                # Adicionar ajuste de arredondamento se necessário
                if 'rounding_adjustment' in vals:
                    vals['description'] = (
                        vals.get('description', '') +
                        vals.pop('rounding_adjustment')
                    )

                svl_vals_list.append(vals)
        else:
            # lot_valuated=False: agregar tudo numa única SVL
            total_qty = sum(quantity_by_lot.values())

            # Tentar obter lot_group através dos lotes
            lot_group = None
            for lot in quantity_by_lot.keys():
                lot_group = self._get_lot_group_for_lot(lot)
                if lot_group:
                    break

            # Fallback: lot_group_id do movimento
            if not lot_group:
                lot_group = self.lot_group_id

            if lot_group:
                _logger.info(
                    f"Venda PCMP (agregado): lot_group={lot_group.name}, pcmp={lot_group.pcmp}"
                )
                # Usar PCMP do grupo de lote
                vals = self.product_id._prepare_out_svl_vals(
                    total_qty, self.company_id, lot_group=lot_group
                )
            else:
                # Usar PCMP do produto
                vals = self.product_id._prepare_out_svl_vals(total_qty, self.company_id)

            vals.update(self._prepare_common_svl_vals())

            # Adicionar lot_group_id se definido
            if lot_group:
                vals['lot_group_id'] = lot_group.id

            # Adicionar ajuste de arredondamento se necessário
            if 'rounding_adjustment' in vals:
                vals['description'] = (
                    vals.get('description', '') +
                    vals.pop('rounding_adjustment')
                )

            svl_vals_list.append(vals)

        return svl_vals_list
