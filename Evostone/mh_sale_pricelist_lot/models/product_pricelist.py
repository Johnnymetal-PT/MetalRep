# -*- coding: utf-8 -*-

from odoo import api, models


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    def _get_applicable_rules_domain(self, products, date, **kwargs):
        """
        Extend domain to support lot-based filtering.

        CRITICAL: Reads lot_id from CONTEXT (not kwargs) because Odoo 18
        doesn't propagate kwargs through the entire pricelist chain.

        When lot_id is in context, this method adds domain conditions
        to match pricelist items that apply to:
        - The lot's base lot group (base.lot.group)
        - The lot's price group (lot.price.group)

        The domain uses OR logic to include:
        - Rules without lot group restrictions (base_lot_group_id = False)
        - Rules matching the lot's base lot group
        - Rules without price group restrictions (lot_price_group_id = False)
        - Rules matching the lot's price group

        Args:
            products: product.product or product.template recordset
            date: date for validity check
            **kwargs: additional parameters (lot_id NOT passed here - use context!)

        Returns:
            list: Odoo domain for searching applicable pricelist items
        """
        # Get standard domain (product, category, date filters)
        domain = super()._get_applicable_rules_domain(products, date, **kwargs)

        # CRITICAL: Read lot_id from CONTEXT (not kwargs!)
        lot_id = self.env.context.get('lot_id')

        if lot_id:
            lot = self.env['stock.lot'].browse(lot_id)

            # Only add lot filters if lot exists and has necessary fields
            if lot.exists() and hasattr(lot, 'price_group_id'):
                lot_conditions = []

                # Base lot group matching
                # Format: '|' means OR for the next two conditions
                lot_conditions.append('|')
                lot_conditions.append(('base_lot_group_id', '=', False))

                if lot.sudo().price_group_id and hasattr(lot.sudo().price_group_id, 'base_lot_group_id') \
                   and lot.sudo().price_group_id.base_lot_group_id:
                    # Match rules for this specific base lot group
                    lot_conditions.append(
                        ('base_lot_group_id', '=', lot.sudo().price_group_id.base_lot_group_id.id)
                    )
                else:
                    # If lot has no base group, only match rules without base group restriction
                    lot_conditions.append(('base_lot_group_id', '=', False))

                # Lot price group matching
                lot_conditions.append('|')
                lot_conditions.append(('lot_price_group_id', '=', False))

                if lot.sudo().price_group_id:
                    # Match rules for this specific lot price group
                    lot_conditions.append(
                        ('lot_price_group_id', '=', lot.sudo().price_group_id.id)
                    )
                else:
                    # If lot has no price group, only match rules without price group restriction
                    lot_conditions.append(('lot_price_group_id', '=', False))

                domain.extend(lot_conditions)

        return domain

    def _get_product_rule(self, product, **kwargs):
        """
        Override para aceitar e propagar lot_id.

        Odoo 18 original: _get_product_rule(product, quantity=1.0, uom=None, date=False)
        Nossa versão aceita: lot_id nos kwargs e propaga para _compute_price_rule

        Args:
            product: product.product recordset
            **kwargs: quantity, uom, date, lot_id, etc.

        Returns:
            int: ID do pricelist.item que aplica (ou False)
        """
        # lot_id já está nos kwargs se foi passado
        # Apenas propagar para o parent
        return super()._get_product_rule(product, **kwargs)

    def _compute_price_rule(self, products, *args, **kwargs):
        """
        Override para aceitar e propagar kwargs (incluindo lot_id).

        Assinatura flexível com *args para aceitar todas as variações de chamada:
        - _compute_price_rule(products, qty)
        - _compute_price_rule(products, qty, currency, uom, date, ...)
        - _compute_price_rule(products, *args, compute_price=False, **kwargs)

        Args:
            products: product.product recordset
            *args: argumentos posicionais variáveis (qty, currency, uom, date, etc.)
            **kwargs: lot_id, compute_price, e outros kwargs

        Returns:
            dict: {product.id: (price, pricelist_item.id)} para cada produto
        """
        # lot_id está em kwargs, apenas passar através da chain
        # O _get_applicable_rules_domain vai usar lot_id para filtrar
        return super()._compute_price_rule(products, *args, **kwargs)
