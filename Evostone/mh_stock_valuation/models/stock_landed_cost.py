# -*- coding: utf-8 -*-

from odoo import models, api, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class StockLandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    def get_valuation_lines(self):
        """
        Override para incluir produtos com método PCMP.

        O Odoo original só aceita 'fifo' e 'average'.
        Adicionamos 'pcmp' à lista de métodos válidos.
        """
        self.ensure_one()
        lines = []

        for move in self._get_targeted_move_ids():
            # MODIFICAÇÃO: Adicionar 'pcmp' aos métodos aceites
            if move.product_id.cost_method not in ('fifo', 'average', 'pcmp'):
                continue
            if move.state == 'cancel':
                continue
            if not move.quantity:
                continue

            qty = move.product_uom._compute_quantity(move.quantity, move.product_id.uom_id)

            # Para produtos com forma física (blocos, placas, strips, ladrilhos),
            # o peso é proporcional à área (m²) pois têm a mesma densidade e espessura.
            # Usar qty directamente como peso para distribuição correcta por peso.
            # Para produtos com forma física (blocos, placas, strips, ladrilhos),
            # peso e volume são proporcionais à área (m²) pois têm a mesma
            # densidade e espessura. Usar qty directamente para distribuição
            # correcta por peso e por volume.
            product_form = move.product_id.product_form
            if product_form and product_form != 'none':
                weight = qty
                volume = qty
            else:
                weight = move.product_id.weight * qty
                volume = move.product_id.volume * qty

            vals = {
                'product_id': move.product_id.id,
                'move_id': move.id,
                'quantity': qty,
                'former_cost': sum(move._get_stock_valuation_layer_ids().mapped('value')),
                'weight': weight,
                'volume': volume,
            }
            lines.append(vals)

        if not lines:
            target_model_descriptions = dict(self._fields['target_model']._description_selection(self.env))
            raise UserError(_(
                "You cannot apply landed costs on the chosen %s(s). "
                "Landed costs can only be applied for products with FIFO, average or PCMP costing method.",
                target_model_descriptions[self.target_model]
            ))
        return lines

    def button_validate(self):
        """
        Override para suportar PCMP na validação de custos adicionais.

        IMPORTANTE para PCMP:
        O Odoo standard prorratea o LC baseado em remaining_qty/quantity.
        Para PCMP, precisamos do valor TOTAL aplicado ao stock remanescente,
        e o ajuste CMV é feito separadamente no import.document.

        Exemplo:
        - Entrada: 100 un × 10 = 1000
        - Venda: 20 un (remaining_qty = 80)
        - LC: 300
        - Odoo standard: SVL = 300 × 80/100 = 240 (ERRADO para PCMP)
        - PCMP correto: SVL = 300 (TOTAL)

        A correcção é feita via _adjust_pcmp_landed_cost_svl após o super().
        """
        # 1. Guardar SVLs existentes antes do super()
        existing_svl_ids = self.env['stock.valuation.layer'].sudo().search([
            ('stock_landed_cost_id', 'in', self.ids)
        ]).ids

        # 2. Guardar valores originais PCMP ANTES do super
        pcmp_adjustments = {}
        for cost in self:
            for line in cost.valuation_adjustment_lines:
                product = line.move_id.product_id
                if product.cost_method == 'pcmp':
                    # Buscar lot_group_id da SVL de entrada original
                    entry_svl = line.move_id.stock_valuation_layer_ids.filtered(
                        lambda l: l.quantity > 0
                    )[:1]
                    lot_group_id = entry_svl.lot_group_id.id if entry_svl and entry_svl.lot_group_id else False

                    pcmp_adjustments[(cost.id, line.id)] = {
                        'additional_landed_cost': line.additional_landed_cost,
                        'product_id': product.id,
                        'move_id': line.move_id.id,
                        'lot_group_id': lot_group_id,
                    }

        # 3. super()
        res = super().button_validate()

        # 4. Encontrar novas SVLs criadas e copiar lot_group_id da SVL pai
        new_svls = self.env['stock.valuation.layer'].sudo().search([
            ('stock_landed_cost_id', 'in', self.ids),
            ('id', 'not in', existing_svl_ids),
        ])
        for svl in new_svls:
            if svl.stock_valuation_layer_id and svl.stock_valuation_layer_id.lot_group_id:
                svl.lot_group_id = svl.stock_valuation_layer_id.lot_group_id.id

        # 5. Corrigir SVLs PCMP para usar valor total (não prorated)
        self._adjust_pcmp_landed_cost_svl(pcmp_adjustments)

        # 6. Recalcular PCMP
        self._update_pcmp_prices()
        return res

    def _adjust_pcmp_landed_cost_svl(self, pcmp_adjustments):
        """
        Corrige SVLs de Landed Cost para produtos PCMP.

        O Odoo standard cria SVL com valor prorated (remaining_qty/quantity).
        Para PCMP, precisamos do valor total do LC aplicado ao stock.
        O ajuste CMV é tratado separadamente pelo import.document.

        Inclui lot_group_id no domínio de busca para garantir precisão
        quando o mesmo produto existe em vários base.lot.group.

        :param pcmp_adjustments: dict com {(cost_id, line_id): {
            'additional_landed_cost': valor,
            'product_id': int,
            'move_id': int,
            'lot_group_id': int or False,
        }}
        """
        if not pcmp_adjustments:
            return

        import logging
        _logger = logging.getLogger(__name__)

        SVL = self.env['stock.valuation.layer'].sudo()
        processed_svl_ids = set()

        for (cost_id, line_id), data in pcmp_adjustments.items():
            target_value = data['additional_landed_cost']
            product_id = data['product_id']
            move_id = data['move_id']
            lot_group_id = data.get('lot_group_id', False)

            # Buscar SVL criado pelo Landed Cost para este produto/move/lot_group
            # Excluir SVLs já processados para evitar sobrescrita quando
            # múltiplas linhas de custo referenciam o mesmo produto/move
            domain = [
                ('stock_landed_cost_id', '=', cost_id),
                ('product_id', '=', product_id),
                ('stock_move_id', '=', move_id),
                ('lot_group_id', '=', lot_group_id),
            ]
            if processed_svl_ids:
                domain.append(('id', 'not in', list(processed_svl_ids)))

            lc_svl = SVL.search(domain, limit=1)

            if not lc_svl:
                # Fallback sem lot_group_id (caso a SVL não tenha sido propagada)
                domain_fallback = [
                    ('stock_landed_cost_id', '=', cost_id),
                    ('product_id', '=', product_id),
                    ('stock_move_id', '=', move_id),
                ]
                if processed_svl_ids:
                    domain_fallback.append(('id', 'not in', list(processed_svl_ids)))
                lc_svl = SVL.search(domain_fallback, limit=1)

            if not lc_svl:
                # Odoo standard NÃO cria SVL para adj_lines cujo stock_move já
                # tem quantity_svl=0 (totalmente consumido antes do LC). Para
                # PCMP, isto deixa o SVL pool desalinhado da contabilidade: o
                # account.move debita 223 pelo total, mas o SVL pool fica em
                # falta de `additional_landed_cost`.
                #
                # CRIAR SVL compensatório para alinhar pool com accounting e
                # manter PCMP correcto. A parte vendida será depois reconhecida
                # como CMV pelo import.document.adjustment via SVL negativo.
                cost = self.browse(cost_id).exists()
                if not cost or not cost.account_move_id:
                    continue

                move = self.env['stock.move'].sudo().browse(move_id)
                svl_vals = {
                    'company_id': move.company_id.id or cost.company_id.id,
                    'product_id': product_id,
                    'stock_move_id': move_id,
                    'stock_landed_cost_id': cost_id,
                    'quantity': 0.0,
                    'unit_cost': 0.0,
                    'value': target_value,
                    'description': _(
                        "LC compensação (move consumido) - %s"
                    ) % cost.name,
                    'account_move_id': cost.account_move_id.id,
                }
                if lot_group_id:
                    svl_vals['lot_group_id'] = lot_group_id

                new_svl = SVL.create(svl_vals)
                processed_svl_ids.add(new_svl.id)
                _logger.info(
                    f"PCMP LC SVL compensatório criado: produto {product_id}, "
                    f"move {move_id}, lot_group {lot_group_id}, value={target_value:.2f}"
                )
                continue

            processed_svl_ids.add(lc_svl.id)
            current_value = lc_svl.value
            difference = target_value - current_value

            if abs(difference) < 0.01:
                continue

            # Corrigir o valor do SVL para o valor total
            lc_svl.write({'value': target_value})

            _logger.info(
                f"PCMP LC SVL corrigido: produto {product_id}, lot_group {lot_group_id}, "
                f"valor {current_value:.2f} → {target_value:.2f} (diff: {difference:.2f})"
            )

    def _update_pcmp_prices(self):
        """
        Força recálculo do PCMP após custos adicionais.

        O PCMP é um campo COMPUTED que calcula automaticamente a partir das SVLs.
        Como o button_validate() já copia lot_group_id para as novas SVLs de
        landed cost, o campo computed pcmp irá incluir esses valores quando
        for recalculado.

        Este método apenas:
        1. Identifica quais lot_groups e produtos foram afectados
        2. Invalida o cache para forçar recálculo do pcmp computed
        """
        for cost in self.filtered(lambda c: c.state == 'done'):
            # Identificar lot_groups e produtos afectados
            affected_lot_groups = self.env['base.lot.group']
            affected_products = self.env['product.product']

            for line in cost.valuation_adjustment_lines:
                product = line.move_id.product_id
                move = line.move_id

                # Só processar produtos com método PCMP
                if product.cost_method != 'pcmp':
                    continue

                # Verificar se SVL original tem lot_group_id
                svl = move.stock_valuation_layer_ids.filtered(
                    lambda l: l.quantity > 0  # SVL de entrada
                )[:1]

                if svl and svl.lot_group_id:
                    affected_lot_groups |= svl.lot_group_id
                else:
                    affected_products |= product

            # Invalidar cache e forçar recálculo do pcmp para lot_groups
            if affected_lot_groups:
                affected_lot_groups.invalidate_recordset(['pcmp'])
                affected_lot_groups.modified(['stock_valuation_layer_ids'])
                # Aceder ao campo para forçar recálculo
                _ = affected_lot_groups.mapped('pcmp')

            # Invalidar cache e forçar recálculo do pcmp para produtos
            if affected_products:
                affected_products.invalidate_recordset(['pcmp'])
                # Aceder ao campo para forçar recálculo
                _ = affected_products.mapped('pcmp')


class StockValuationAdjustmentLines(models.Model):
    _inherit = 'stock.valuation.adjustment.lines'

    def _create_accounting_entries(self, move, qty_out):
        """
        Override para bloquear lançamentos "already out" em produtos PCMP.

        O Odoo standard cria lançamentos que movem valor de stock para CMV
        para a parte já vendida (qty_out > 0). Para PCMP, este ajuste é feito
        separadamente pelo import.document._create_cmv_adjustment() que:
        - Filtra por lot_group_id (FIFO não é lot_group-aware)
        - Usa a quantidade importada (import document) como base, não a recebida

        Forçar qty_out=0 faz com que TODO o LC fique em stock,
        e o nosso mecanismo trata o CMV correctamente.
        """
        if self.product_id.cost_method == 'pcmp':
            qty_out = 0
        return super()._create_accounting_entries(move, qty_out)
