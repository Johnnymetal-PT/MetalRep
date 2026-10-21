# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    # Extend applied_on selection with lot group options
    applied_on = fields.Selection(
        selection_add=[
            ('4_base_lot_group', 'Grupo Base Lote'),
            ('5_lot_price_group', 'Grupo Preço Lote'),
        ],
        ondelete={
            '4_base_lot_group': 'cascade',
            '5_lot_price_group': 'cascade',
        }
    )

    # Extend display_applied_on selection for UI
    display_applied_on = fields.Selection(
        selection_add=[
            ('4_base_lot_group', 'Grupo Base Lote'),
            ('5_lot_price_group', 'Grupo Preço Lote'),
        ],
        ondelete={
            '4_base_lot_group': 'set default',
            '5_lot_price_group': 'set default',
        }
    )

    # New reference fields for lot groups
    base_lot_group_id = fields.Many2one(
        'base.lot.group',
        string='Grupo Base Lote',
        ondelete='cascade',
        index=True,
        help='Aplicar esta regra de pricelist a todos os lotes pertencentes a este grupo base. '
             'Grupos base de lote são identificados por produto e nome base do lote (ex: CARRARA_WHITE).'
    )

    lot_price_group_id = fields.Many2one(
        'lot.price.group',
        string='Grupo Preço Lote',
        ondelete='cascade',
        index=True,
        help='Aplicar esta regra de pricelist a lotes com dimensões específicas. '
             'Grupos de preço de lote são identificados por produto, nome base do lote e dimensões exatas '
             '(ex: CARRARA_WHITE-3.00x1.50x0.02).'
    )

    @api.constrains('applied_on', 'categ_id', 'product_tmpl_id', 'product_id',
                    'base_lot_group_id', 'lot_price_group_id')
    def _check_product_consistency(self):
        """Extend validation to include lot group fields"""
        super()._check_product_consistency()

        for item in self:
            if item.applied_on == '4_base_lot_group' and not item.base_lot_group_id:
                raise ValidationError(_(
                    "Por favor especifique um grupo base de lote para esta regra de pricelist.\n"
                    "Grupos base de lote identificam lotes por produto e nome base (ex: CARRARA_WHITE)."
                ))
            elif item.applied_on == '5_lot_price_group' and not item.lot_price_group_id:
                raise ValidationError(_(
                    "Por favor especifique um grupo de preço de lote para esta regra de pricelist.\n"
                    "Grupos de preço de lote identificam lotes por dimensões específicas."
                ))

    @api.onchange('display_applied_on')
    def _onchange_display_applied_on(self):
        """Clear irrelevant fields when display_applied_on changes"""
        super()._onchange_display_applied_on()

        # Map display to applied_on and clear conflicting fields
        if self.display_applied_on == '4_base_lot_group':
            self.applied_on = '4_base_lot_group'
            self.categ_id = False
            self.product_tmpl_id = False
            self.product_id = False
            self.lot_price_group_id = False
        elif self.display_applied_on == '5_lot_price_group':
            self.applied_on = '5_lot_price_group'
            self.categ_id = False
            self.product_tmpl_id = False
            self.product_id = False
            self.base_lot_group_id = False

    @api.onchange('applied_on')
    def _onchange_applied_on(self):
        """Clear irrelevant fields when applied_on changes directly"""
        if self.applied_on == '4_base_lot_group':
            self.categ_id = False
            self.product_tmpl_id = False
            self.product_id = False
            self.lot_price_group_id = False
        elif self.applied_on == '5_lot_price_group':
            self.categ_id = False
            self.product_tmpl_id = False
            self.product_id = False
            self.base_lot_group_id = False

    def _is_applicable_for(self, product, qty_in_product_uom):
        """
        Check if this pricelist rule applies to the product/lot combination.

        CRITICAL: Odoo 18's signature is (product, qty_in_product_uom) - NO kwargs!
        We must read lot_id from CONTEXT instead.

        Now supports lot-based rules:
        - 4_base_lot_group: Applies to all lots in a base lot group
        - 5_lot_price_group: Applies to lots with specific dimensions

        Args:
            product: product.product recordset
            qty_in_product_uom: quantity in product UOM (for min_quantity check)

        Returns:
            bool: True if rule applies, False otherwise
        """
        self.ensure_one()

        # Standard applicability check (product, category, quantity, date)
        is_applicable = super()._is_applicable_for(product, qty_in_product_uom)

        if not is_applicable:
            _logger.info(
                f"❌ [IS_APPLICABLE] Regra {self.id} NÃO aplicável (super retornou False)"
            )
            return False

        # If this rule is not lot-based, it applies
        if self.applied_on not in ['4_base_lot_group', '5_lot_price_group']:
            return True

        # CRITICAL: Read lot_id from CONTEXT (not kwargs!)
        lot_id = self.env.context.get('lot_id')

        _logger.info(
            f"🔍 [IS_APPLICABLE] Regra {self.id}, Applied_on: {self.applied_on}, "
            f"Lot_id context: {lot_id}"
        )

        if self.applied_on == '4_base_lot_group':
            # Rule applies to base lot group - must have lot_id with matching base group
            if not lot_id:
                _logger.info(f"❌ [IS_APPLICABLE] Base lot group rule mas lot_id não existe no context")
                return False

            lot = self.env['stock.lot'].browse(lot_id)

            # Check if lot belongs to a price group with this base group
            if not lot.exists() or not hasattr(lot, 'price_group_id'):
                _logger.info(f"❌ [IS_APPLICABLE] Lot não existe ou não tem price_group_id")
                return False

            if not lot.sudo().price_group_id or not lot.sudo().price_group_id.base_lot_group_id:
                _logger.info(f"❌ [IS_APPLICABLE] Lot sem price_group ou base_lot_group")
                return False

            result = lot.sudo().price_group_id.base_lot_group_id == self.base_lot_group_id

            _logger.info(
                f"{'✅' if result else '❌'} [IS_APPLICABLE] Base lot group match: "
                f"Lot base group: {lot.sudo().price_group_id.base_lot_group_id.name}, "
                f"Rule base group: {self.base_lot_group_id.name}"
            )

            return result

        elif self.applied_on == '5_lot_price_group':
            # Rule applies to specific lot price group - must have lot_id with matching price group
            if not lot_id:
                _logger.info(f"❌ [IS_APPLICABLE] Lot price group rule mas lot_id não existe no context")
                return False

            lot = self.env['stock.lot'].browse(lot_id)

            # Check if lot belongs to this price group
            if not lot.exists() or not hasattr(lot, 'price_group_id'):
                _logger.info(f"❌ [IS_APPLICABLE] Lot não existe ou não tem price_group_id")
                return False

            if not lot.sudo().price_group_id:
                _logger.info(f"❌ [IS_APPLICABLE] Lot sem price_group")
                return False

            result = lot.sudo().price_group_id == self.lot_price_group_id

            _logger.info(
                f"{'✅' if result else '❌'} [IS_APPLICABLE] Lot price group match: "
                f"Lot price group: {lot.sudo().price_group_id.name}, "
                f"Rule price group: {self.lot_price_group_id.name}"
            )

            return result

        return True

    def _get_lot_cost(self, lot, product):
        """
        Obtém o custo do lote com hierarquia de fallback clara.

        Esta função implementa uma prioridade inteligente para determinar
        qual custo usar quando um lote está presente:

        HIERARQUIA DE FALLBACK:
        1. lot.pcmp (Preço Custo Médio Ponderado)
           - Apenas se produto usa método PCMP (uses_pcmp=True)
           - Apenas se pcmp > 0 (custo válido)
           - Mais preciso para produtos com compras múltiplas

        2. lot.standard_price (Custo Padrão do Lote)
           - Custo específico configurado para este lote
           - Pode ser diferente do custo base do produto
           - Usado para lotes com custos especiais

        3. lot.price_group_id.standard_price (Custo do Grupo de Preço)
           - Custo compartilhado por lotes com mesmas dimensões
           - Útil quando lotes similares têm mesmo custo

        4. product.standard_price (Custo Base do Produto)
           - Fallback final quando nenhum custo específico existe
           - Garante que sempre há um custo disponível

        Args:
            lot: stock.lot recordset (deve estar carregado)
            product: product.product recordset

        Returns:
            float: Custo a ser usado como base para cálculos

        Examples:
            # Produto PCMP com lote tendo PCMP
            lot.uses_pcmp = True, lot.pcmp = 1250.00
            → Retorna: 1250.00 (prioridade 1)

            # Produto normal com custo específico de lote
            lot.standard_price = 1100.00, product.standard_price = 1000.00
            → Retorna: 1100.00 (prioridade 2)

            # Lote sem custo, grupo com custo
            lot.price_group_id.standard_price = 900.00
            → Retorna: 900.00 (prioridade 3)

            # Lote sem nenhum custo específico
            product.standard_price = 800.00
            → Retorna: 800.00 (prioridade 4)
        """
        self.ensure_one()

        # Prioridade 1: PCMP (Preço Custo Médio Ponderado)
        # Apenas para produtos que usam este método de custeio
        if (hasattr(lot, 'uses_pcmp') and lot.uses_pcmp and
            hasattr(lot, 'pcmp') and lot.pcmp and lot.pcmp > 0):
            _logger.info(
                f"💰 [GET_LOT_COST] Prioridade 1: Usando lot.pcmp = {lot.pcmp:.2f} "
                f"(Lote: {lot.name}, Produto: {product.display_name})"
            )
            return lot.pcmp

        # Prioridade 2: Custo específico do lote
        if hasattr(lot, 'standard_price') and lot.standard_price and lot.standard_price > 0:
            _logger.info(
                f"💰 [GET_LOT_COST] Prioridade 2: Usando lot.standard_price = {lot.standard_price:.2f} "
                f"(Lote: {lot.name}, Produto: {product.display_name})"
            )
            return lot.standard_price

        # Prioridade 3: Custo do grupo de preço
        if (hasattr(lot, 'price_group_id') and lot.sudo().price_group_id and
            hasattr(lot.sudo().price_group_id, 'standard_price') and
            lot.sudo().price_group_id.standard_price and lot.sudo().price_group_id.standard_price > 0):
            _logger.info(
                f"💰 [GET_LOT_COST] Prioridade 3: Usando lot.price_group_id.standard_price = "
                f"{lot.sudo().price_group_id.standard_price:.2f} "
                f"(Grupo: {lot.sudo().price_group_id.name}, Lote: {lot.name})"
            )
            return lot.sudo().price_group_id.standard_price

        # Prioridade 4: Fallback para custo base do produto
        _logger.info(
            f"⬇️ [GET_LOT_COST] Prioridade 4 (Fallback): Usando product.standard_price = "
            f"{product.standard_price:.2f} "
            f"(Lote: {lot.name} sem custo específico, Produto: {product.display_name})"
        )
        return product.standard_price

    def _compute_price(self, product, quantity, uom, date, currency):
        """
        Override para usar lot_id.list_price_lot e lot_id.standard_price como base em cálculos.

        PROBLEMA RESOLVIDO #1:
        Quando regra de pricelist usa percentagem/fórmula para lot groups, o Odoo padrão
        usa product.lst_price como base, ignorando lot_id.list_price_lot.

        PROBLEMA RESOLVIDO #2:
        "Expected singleton" error quando pricelist_item_id está vazio.
        Odoo pode chamar _compute_price() com recordset vazio durante
        recálculo de preços (action_update_prices).

        PROBLEMA RESOLVIDO #3:
        Tipos nativos (0_product_variant, 1_product, 2_product_category, 3_global)
        agora também consideram lot.list_price_lot quando um lote está presente,
        garantindo precificação consistente em TODAS as regras de pricelist.

        PROBLEMA RESOLVIDO #4 (NOVO):
        Fórmulas com base='standard_price' agora usam custo específico do lote
        (lot.pcmp ou lot.standard_price) em vez de sempre usar product.standard_price.
        Isso permite markup sobre custo real de cada lote individual.

        SOLUÇÃO:
        1. Verificar se recordset não está vazio ANTES de ensure_one()
        2. Se vazio → usar super()._compute_price() (fallback padrão Odoo)
        3. Ler lot_id do context (já é passado via _compute_pricelist_item_id)
        4. Se lot existe E compute_price é percentage/formula:
           a) Para tipos lot-based (4, 5): usar lot.list_price_lot
           b) Para tipos nativos (0, 1, 2, 3):
              - base='list_price' → usar lot.list_price_lot
              - base='standard_price' → usar lot cost (via _get_lot_cost)
              - outras bases → usar lógica Odoo padrão
        5. Senão, usar lógica padrão do Odoo

        Suporta todos os compute_price:
        - 'fixed': retorna fixed_price (não depende de base)
        - 'percentage': base_price (discount vai para sale.order.line.discount)
        - 'formula': base_price com discount + surcharge

        Suporta todas as bases (formula only):
        - 'list_price': usa lot.list_price_lot quando lote presente
        - 'standard_price': usa lot cost (pcmp/standard_price) quando lote presente
        - 'pricelist': recursivo (Odoo padrão)
        - outras: Odoo padrão

        Args:
            product: product.product recordset
            quantity: quantidade
            uom: unidade de medida
            date: data para cálculo
            currency: moeda

        Returns:
            float: Preço calculado
        """
        # CRITICAL FIX: Handle empty recordsets to prevent "Expected singleton" error
        # Odoo pode chamar este método com recordset vazio quando pricelist_item_id = False
        if not self:
            # Recordset vazio - usar implementação padrão do Odoo
            return super()._compute_price(product, quantity, uom, date, currency)

        self.ensure_one()

        # Ler lot_id do contexto (passado via _compute_pricelist_item_id)
        lot_id = self.env.context.get('lot_id')

        _logger.info(
            f"💰 [COMPUTE_PRICE] Item: {self.id}, Applied_on: {self.applied_on}, "
            f"Compute_price: {self.compute_price}, Lot_id context: {lot_id}"
        )

        # Se lot_id existe E compute_price é percentage ou formula
        # (fixed price não depende de base, então não precisa de ajuste)
        if lot_id and self.compute_price in ['percentage', 'formula']:
            lot = self.env['stock.lot'].browse(lot_id)

            _logger.info(
                f"📦 [COMPUTE_PRICE] Lot encontrado: {lot.name if lot.exists() else 'NOT EXISTS'}, "
                f"list_price_lot: {lot.list_price_lot if lot.exists() and hasattr(lot, 'list_price_lot') else 'N/A'}"
            )

            # Se lot existe e tem preço definido, usar como base
            if lot.exists() and hasattr(lot, 'list_price_lot') and lot.list_price_lot:
                base_price = lot.list_price_lot

                # ===== TIPOS LOT-BASED (4, 5) - Comportamento Existente =====
                if self.applied_on in ['4_base_lot_group', '5_lot_price_group']:
                    _logger.info(
                        f"🎯 [COMPUTE_PRICE LOT-BASED] Tipo lot-based ({self.applied_on}), "
                        f"usando lot.list_price_lot: {base_price}"
                    )

                    # Aplicar cálculo baseado no método
                    if self.compute_price == 'percentage':
                        # Aplicar percent (comportamento standard do Odoo).
                        # _compute_discount calcula a partir da diferença entre
                        # _compute_price (com percent) e _compute_base_price (sem percent).
                        price = base_price * (1 - (self.percent_price or 0.0) / 100.0)

                        _logger.info(
                            f"📊 [COMPUTE_PRICE PERCENTAGE LOT] Base: {base_price}, "
                            f"Percent: {self.percent_price}%, Final: {price}"
                        )

                    elif self.compute_price == 'formula':
                        # Fórmula: base × (1 - price_discount/100) + price_surcharge
                        price = base_price * (1 - (self.price_discount / 100.0))
                        price += self.price_surcharge

                        # Aplicar arredondamento se configurado
                        if self.price_round:
                            price = round(price / self.price_round) * self.price_round

                        _logger.info(
                            f"📊 [COMPUTE_PRICE FORMULA LOT] Base: {base_price}, "
                            f"Discount: {self.price_discount}%, Surcharge: {self.price_surcharge}, "
                            f"Final: {price}"
                        )

                    # Converter moeda se necessário
                    if currency and hasattr(product, 'currency_id') and product.currency_id != currency:
                        from odoo import fields
                        old_price = price
                        price = product.currency_id._convert(
                            price, currency, self.env.company, date or fields.Date.today()
                        )
                        _logger.info(f"💱 [COMPUTE_PRICE] Currency conversion: {old_price} -> {price}")

                    return price

                # ===== TIPOS NATIVOS (0, 1, 2, 3) - NOVO COMPORTAMENTO =====
                elif self.applied_on in ['0_product_variant', '1_product', '2_product_category', '3_global']:
                    _logger.info(
                        f"🆕 [COMPUTE_PRICE NATIVE] Tipo nativo ({self.applied_on}), "
                        f"verificando se deve usar lot price..."
                    )

                    # Para percentage: sempre usar lot price como base
                    if self.compute_price == 'percentage':
                        # Aplicar percent (standard Odoo). O `discount` na
                        # sale.order.line é calculado a partir da diferença
                        # entre _compute_price e _compute_base_price.
                        price = base_price * (1 - (self.percent_price or 0.0) / 100.0)

                        _logger.info(
                            f"✅ [COMPUTE_PRICE PERCENTAGE NATIVE] Usando lot.list_price_lot: {base_price}, "
                            f"Percent: {self.percent_price}%, Final: {price}"
                        )

                        # Converter moeda se necessário
                        if currency and hasattr(product, 'currency_id') and product.currency_id != currency:
                            from odoo import fields
                            old_price = price
                            price = product.currency_id._convert(
                                price, currency, self.env.company, date or fields.Date.today()
                            )
                            _logger.info(f"💱 [COMPUTE_PRICE] Currency conversion: {old_price} -> {price}")

                        return price

                    # Para formula: APENAS se base='list_price'
                    elif self.compute_price == 'formula':
                        # Verificar qual base está configurada na regra
                        if self.base == 'list_price':
                            # Usar lot price como base
                            price = base_price * (1 - (self.price_discount / 100.0))
                            price += self.price_surcharge

                            # Aplicar arredondamento se configurado
                            if self.price_round:
                                price = round(price / self.price_round) * self.price_round

                            _logger.info(
                                f"✅ [COMPUTE_PRICE FORMULA NATIVE] Base=list_price, "
                                f"usando lot.list_price_lot: {base_price}, "
                                f"Discount: {self.price_discount}%, Surcharge: {self.price_surcharge}, "
                                f"Final: {price}"
                            )

                            # Converter moeda se necessário
                            if currency and hasattr(product, 'currency_id') and product.currency_id != currency:
                                from odoo import fields
                                old_price = price
                                price = product.currency_id._convert(
                                    price, currency, self.env.company, date or fields.Date.today()
                                )
                                _logger.info(f"💱 [COMPUTE_PRICE] Currency conversion: {old_price} -> {price}")

                            return price

                        elif self.base == 'standard_price':
                            # NOVO: Usar lot cost (pcmp ou standard_price) como base
                            lot_cost = self._get_lot_cost(lot, product)

                            # Aplicar fórmula
                            price = lot_cost * (1 - (self.price_discount / 100.0))
                            price += self.price_surcharge

                            # Aplicar arredondamento se configurado
                            if self.price_round:
                                price = round(price / self.price_round) * self.price_round

                            _logger.info(
                                f"✅ [COMPUTE_PRICE FORMULA NATIVE COST] Base=standard_price, "
                                f"usando custo do lote: {lot_cost:.2f}, "
                                f"Discount: {self.price_discount}%, Surcharge: {self.price_surcharge}, "
                                f"Final: {price:.2f}"
                            )

                            # Converter moeda se necessário
                            if currency and hasattr(product, 'currency_id') and product.currency_id != currency:
                                from odoo import fields
                                old_price = price
                                price = product.currency_id._convert(
                                    price, currency, self.env.company, date or fields.Date.today()
                                )
                                _logger.info(f"💱 [COMPUTE_PRICE] Currency conversion: {old_price:.2f} -> {price:.2f}")

                            return price

                        else:
                            # Base é pricelist ou other - Deixar Odoo processar com sua lógica padrão
                            _logger.info(
                                f"⚠️ [COMPUTE_PRICE FORMULA NATIVE] Base={self.base}, "
                                f"NÃO é list_price nem standard_price, usando super() (Odoo padrão)"
                            )
                            # Cair no fallback abaixo

        # Fallback: usar lógica padrão do Odoo para todos os outros casos
        # - Sem lot_id no contexto
        # - Lot sem list_price_lot
        # - compute_price = 'fixed'
        # - Formula com base != 'list_price'
        _logger.info(
            f"⬇️ [COMPUTE_PRICE] Usando super()._compute_price (fallback padrão Odoo) - "
            f"Lot_id: {lot_id}, Compute: {self.compute_price}, Applied_on: {self.applied_on}"
        )
        return super()._compute_price(product, quantity, uom, date, currency)

    def _compute_base_price(self, product, quantity, uom, date, currency):
        """Override para usar lot.list_price_lot como base quando há lot_id no contexto.

        Necessário para que `_get_pricelist_price_before_discount` (chamado por
        `_get_display_price` e `_compute_discount`) devolva o preço do lote em vez
        de product.list_price. Sem este override:
        - `_get_display_price` faria max(product.list_price, lot_price) e o
          price_unit ficaria preso em product.list_price.
        - `_compute_discount` calcularia o desconto sobre product.list_price.
        """
        if self:
            self.ensure_one()
            rule_base = self.base or 'list_price'
            lot_id = self.env.context.get('lot_id')
            if lot_id and rule_base == 'list_price':
                lot = self.env['stock.lot'].browse(lot_id)
                if lot.exists() and hasattr(lot, 'list_price_lot') and lot.list_price_lot:
                    price = lot.list_price_lot
                    src_currency = product.currency_id
                    if currency and src_currency and src_currency != currency:
                        price = src_currency._convert(
                            price, currency, self.env.company,
                            date or fields.Date.today(),
                        )
                    _logger.info(
                        f"💎 [COMPUTE_BASE_PRICE] lot={lot.name}, "
                        f"list_price_lot={lot.list_price_lot} → base={price}"
                    )
                    return price
        return super()._compute_base_price(product, quantity, uom, date, currency)

    @api.model_create_multi
    def create(self, vals_list):
        """Clear irrelevant fields based on applied_on when creating"""
        for vals in vals_list:
            if vals.get('applied_on') == '4_base_lot_group':
                vals.update({
                    'categ_id': False,
                    'product_tmpl_id': False,
                    'product_id': False,
                    'lot_price_group_id': False,
                })
            elif vals.get('applied_on') == '5_lot_price_group':
                vals.update({
                    'categ_id': False,
                    'product_tmpl_id': False,
                    'product_id': False,
                    'base_lot_group_id': False,
                })

        return super().create(vals_list)

    def write(self, vals):
        """Clear irrelevant fields when applied_on changes"""
        if 'applied_on' in vals:
            if vals['applied_on'] == '4_base_lot_group':
                vals.update({
                    'categ_id': False,
                    'product_tmpl_id': False,
                    'product_id': False,
                    'lot_price_group_id': False,
                })
            elif vals['applied_on'] == '5_lot_price_group':
                vals.update({
                    'categ_id': False,
                    'product_tmpl_id': False,
                    'product_id': False,
                    'base_lot_group_id': False,
                })

        return super().write(vals)

    @api.depends('applied_on', 'base_lot_group_id', 'lot_price_group_id',
                 'categ_id', 'product_tmpl_id', 'product_id', 'display_applied_on')
    def _compute_name(self):
        """
        Override para gerar nome de exibição para regras de pricelist.

        Segue o padrão oficial do Odoo 18, mas adiciona suporte para lot groups
        com mensagens em PORTUGUÊS.

        Gera nomes baseados no tipo de regra (applied_on):
        - 4_base_lot_group: "Grupo Base Lote: [nome]"
        - 5_lot_price_group: "Grupo Preço Lote: [nome]"
        - Outros tipos: usa lógica padrão do Odoo (categoria, produto, variante, global)
        """
        for item in self:
            if item.applied_on == '4_base_lot_group' and item.base_lot_group_id:
                item.name = _("Grupo Base Lote: %s") % item.base_lot_group_id.name
            elif item.applied_on == '5_lot_price_group' and item.lot_price_group_id:
                item.name = _("Grupo Preço Lote: %s") % item.lot_price_group_id.name
            else:
                # Chamar lógica padrão do Odoo para outros casos
                # (categoria, produto, variante, global)
                super()._compute_name()
