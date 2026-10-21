# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # 1. Override _compute_pricelist_item_id para passar lot_id via CONTEXT
    @api.depends('product_id', 'product_uom', 'product_uom_qty', 'lot_id')
    def _compute_pricelist_item_id(self):
        """
        Override para passar lot_id ao pricelist via CONTEXT.

        CRITICAL: Odoo 18's pricelist methods don't accept **kwargs.
        We must use CONTEXT to pass custom data through the chain.

        Flow:
        - pricelist.with_context(lot_id=X) sets context
        - _get_applicable_rules_domain reads from context
        - _is_applicable_for reads from context
        """
        for line in self:
            if not line.product_id or line.display_type or not line.order_id.pricelist_id:
                line.pricelist_item_id = False
            else:
                # CRITICAL: Pass lot_id via CONTEXT (not kwargs!) apenas para fluxo Stone Trading
                pricelist = line.order_id.pricelist_id
                order = line.order_id
                if line.lot_id and (not order or order._mh_stone_gates_apply()):
                    pricelist = pricelist.with_context(lot_id=line.lot_id.id)
                    _logger.info(
                        f"🔍 [PRICELIST] Passando lot_id={line.lot_id.id} ({line.lot_id.name}) "
                        f"via context para pricelist"
                    )

                line.pricelist_item_id = pricelist._get_product_rule(
                    line.product_id,
                    quantity=line.product_uom_qty or 1.0,
                    uom=line.product_uom,
                    date=line._get_order_date(),
                )

                _logger.info(
                    f"🎯 [PRICELIST] Regra encontrada: {line.pricelist_item_id.id if line.pricelist_item_id else 'None'}, "
                    f"Product: {line.product_id.name}, Lot: {line.lot_id.name if line.lot_id else 'None'}"
                )

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        """
        Quando lote muda:
        1. Preencher dimensões do lote SEM atualizar preço (usa skip_lot_price_update flag)
        2. Invalidar cache do pricelist_item_id
        3. Forçar recálculo de pricelist_item_id com novo lot_id
        4. Forçar recálculo de preço usando pricelist

        CRITICAL: Usa context flag 'skip_lot_price_update' para prevenir
        que _update_price_from_lot sobrescreva o preço do pricelist.

        Flow:
        - _onchange_lot_id_dimensions preenche length, width, thickness
        - invalidate_recordset limpa cache
        - _compute_pricelist_item_id busca nova regra via context
        - _reset_price_unit recalcula preço usando pricelist
        """
        _logger.info(
            f"🔄 [ONCHANGE_LOT_ID] Lot mudou para: {self.lot_id.name if self.lot_id else 'None'}, "
            f"Product: {self.product_id.name if self.product_id else 'None'}"
        )

        # CRITICAL: Use context flag to prevent _update_price_from_lot from overwriting
        self.with_context(skip_lot_price_update=True)._onchange_lot_id_dimensions()

        # Forçar recálculo completo do pricelist quando lot muda
        if self.product_id and self.order_id.pricelist_id:
            _logger.info(f"🔄 [ONCHANGE_LOT_ID] Forçando recálculo de pricelist_item_id...")

            # 1. Invalidar cache do pricelist_item_id
            # Isso força o Odoo a recalcular qual regra aplica
            self.invalidate_recordset(['pricelist_item_id'])

            # 2. Recomputar pricelist_item_id com novo lot_id
            # Agora _compute_pricelist_item_id vai passar o lot_id via context
            self._compute_pricelist_item_id()

            _logger.info(
                f"🔄 [ONCHANGE_LOT_ID] Nova regra: {self.pricelist_item_id.id if self.pricelist_item_id else 'None'}"
            )

            # 3. Forçar recálculo de preço com contexto especial
            # O contexto force_price_recomputation ignora preços manuais
            self.with_context(force_price_recomputation=True)._reset_price_unit()

            _logger.info(f"🔄 [ONCHANGE_LOT_ID] Novo price_unit: {self.price_unit}")

    def _onchange_lot_id_dimensions(self):
        """
        Helper method para preencher dimensões do lote sem atualizar preço.

        Chama super() apenas se skip_lot_price_update não está no contexto.
        Quando skip_lot_price_update=True, apenas preenche dimensões.

        Isso permite separar o preenchimento de dimensões da atualização de preço,
        evitando que _update_price_from_lot sobrescreva o preço do pricelist.
        """
        if not self.env.context.get('skip_lot_price_update'):
            # Normal flow: chamar super que atualiza dimensões E preço
            return super()._onchange_lot_id()

        # Skip price update flow: apenas preencher dimensões do lote
        # Código copiado do mh_sale._onchange_lot_id (sem a parte do preço)
        if self.lot_id:
            # Preencher length, width, thickness do lote
            if hasattr(self.lot_id, 'length'):
                self.length = self.lot_id.length
            if hasattr(self.lot_id, 'width'):
                self.width = self.lot_id.width
            if hasattr(self.lot_id, 'thickness'):
                self.thickness = self.lot_id.thickness
            # NÃO atualizar price_unit aqui!

    def _reset_price_unit(self):
        """
        Override para adicionar fallback para lot_id.list_price_lot.

        PROBLEMA RESOLVIDO #1:
        Quando um pricelist NÃO tem regra específica para o produto,
        o Odoo 18 padrão faz fallback direto para product.lst_price,
        ignorando completamente o lot_id.list_price_lot.

        PROBLEMA RESOLVIDO #2:
        Quando existe regra de pricelist lot-based com percentage,
        o context com lot_id é perdido durante a chamada a _compute_price().

        SOLUÇÃO:
        1. Passar lot_id via context quando chamar super()._reset_price_unit()
        2. Isso garante que o context esteja disponível em TODA a cadeia de métodos
        3. Após super(), verificar se precisa fazer fallback para lot price

        Hierarquia de preços (após este fix):
        1. Pricelist rule (lot-based, product-based, category, global)
        2. lot_id.list_price_lot (se lot selecionado e tem preço)
        3. product.lst_price (fallback final padrão do Odoo)

        CRITICAL: Este método garante que:
        - O context com lot_id está presente durante TODO o cálculo de preços
        - O preço do lote tem prioridade quando não existe regra de pricelist
        """
        # Fluxo Stone Trading (MZ) vs Standard (PT): nas empresas standard/Portugal não usar lot pricing
        order = self.order_id or self.env['sale.order'].browse(self.env.context.get('order_id'))
        is_pt_flow = order and not order._mh_stone_gates_apply()

        # CRITICAL: Se existe lot_id e é fluxo Stone Trading, passar via context para TODA a cadeia de métodos
        if self.lot_id and not is_pt_flow:
            _logger.info(
                f"🔑 [RESET_PRICE_UNIT] Injetando lot_id={self.lot_id.id} no context antes de super()"
            )
            # Chamar super() com context contendo lot_id
            self.with_context(lot_id=self.lot_id.id)._reset_price_unit_with_context()
        else:
            # Sem lot_id ou fluxo PT standard, chamar normalmente
            super()._reset_price_unit()

        _logger.info(
            f"💲 [RESET_PRICE_UNIT] Após super(): price_unit={self.price_unit}, "
            f"pricelist_item_id={self.pricelist_item_id.id if self.pricelist_item_id else 'None'}, "
            f"lot_id={self.lot_id.name if self.lot_id else 'None'}"
        )

        if is_pt_flow:
            return

        # Se não existe pricelist_item_id (nenhuma regra aplicável)
        # E existe lot_id com preço definido
        # Então usar preço do lote em vez de preço do produto
        if not self.pricelist_item_id:
            if self.lot_id and hasattr(self.lot_id, 'list_price_lot'):
                # Apenas usar preço do lote se for > 0
                # Se for 0, manter o preço já definido pelo super() (product.lst_price)
                if self.lot_id.list_price_lot:
                    old_price = self.price_unit
                    self.price_unit = self.lot_id.list_price_lot
                    _logger.info(
                        f"📦 [RESET_PRICE_UNIT] Fallback para lot price: "
                        f"{old_price} -> {self.price_unit}"
                    )

    def _reset_price_unit_with_context(self):
        """
        Helper method que chama super()._reset_price_unit() preservando o context.

        Este método é chamado via with_context(lot_id=X), garantindo que
        o lot_id esteja disponível em TODA a cadeia de chamadas do pricelist.
        """
        super(SaleOrderLine, self)._reset_price_unit()

    def _get_pricelist_price(self):
        """Injecta lot_id no context para `_compute_price`.

        Necessário em fluxos como `_compute_discount` que chamam directamente
        este método sem passar pelo `_reset_price_unit` (onde o lot_id é
        normalmente injectado).
        """
        self.ensure_one()
        order = self.order_id or self.env['sale.order'].browse(self.env.context.get('order_id'))
        if order and not order._mh_stone_gates_apply():
            return super()._get_pricelist_price()
        if self.lot_id:
            return super(
                SaleOrderLine, self.with_context(lot_id=self.lot_id.id)
            )._get_pricelist_price()
        return super()._get_pricelist_price()

    def _get_pricelist_price_before_discount(self):
        """Injecta lot_id no context para que `_compute_base_price` use lot.list_price_lot.

        Sem isto, `_get_display_price` faria max(product.list_price, pricelist_price)
        e o price_unit ficaria no product.list_price quando este for superior ao
        preço do lote.
        """
        self.ensure_one()
        order = self.order_id or self.env['sale.order'].browse(self.env.context.get('order_id'))
        if order and not order._mh_stone_gates_apply():
            return super()._get_pricelist_price_before_discount()
        if self.lot_id:
            return super(
                SaleOrderLine, self.with_context(lot_id=self.lot_id.id)
            )._get_pricelist_price_before_discount()
        return super()._get_pricelist_price_before_discount()
