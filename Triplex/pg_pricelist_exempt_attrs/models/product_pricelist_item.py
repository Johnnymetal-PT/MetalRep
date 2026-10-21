# -*- coding: utf-8 -*-
"""Exclui da regra de preço os suplementos de determinados atributos.

Uma regra standard aplica-se ao preço da variante com todos os suplementos de atributo
somados. Aqui, se a lista tiver atributos isentos, a regra é calculada sobre o preço sem
esses suplementos e estes são somados no fim, sem alteração:

    preço = regra(preço da variante - suplementos isentos) + suplementos isentos

Só se aplica a regras de percentagem/fórmula com base no Preço de Venda (list_price) e a
variantes (product.product). Nos restantes casos o cálculo é o standard.
"""
from odoo import models


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    def _pg_applies_exempt(self, product):
        self.ensure_one()
        return bool(
            self.pricelist_id.pg_exempt_attribute_ids
            and product._name == 'product.product'
            and self.compute_price in ('percentage', 'formula')
            and (self.base or 'list_price') == 'list_price'
        )

    def _pg_exempt_amount(self, product, uom, date, currency):
        """Soma dos suplementos dos atributos isentos, na UoM e moeda do cálculo da regra."""
        self.ensure_one()
        attributes = self.pricelist_id.pg_exempt_attribute_ids
        extra = sum(
            product.product_template_attribute_value_ids
            .filtered(lambda ptav: ptav.attribute_id in attributes)
            .mapped('price_extra')
        )
        if not extra:
            return 0.0
        if uom and product.uom_id != uom:
            extra = product.uom_id._compute_price(extra, uom)
        if currency and product.currency_id != currency:
            extra = product.currency_id._convert(
                extra, currency, self.env.company, date, round=False)
        return extra

    def _compute_base_price(self, product, quantity, uom, date, currency):
        price = super()._compute_base_price(product, quantity, uom, date, currency)
        if self and self.env.context.get('pg_skip_exempt') and self._pg_applies_exempt(product):
            price -= self._pg_exempt_amount(product, uom, date, currency)
        return price

    def _compute_price(self, product, quantity, uom, date, currency=None):
        if self:
            self.ensure_one()
            product.ensure_one()
            if self._pg_applies_exempt(product):
                currency = currency or self.currency_id or self.env.company.currency_id
                exempt = self._pg_exempt_amount(product, uom, date, currency)
                if exempt:
                    price = super(ProductPricelistItem, self.with_context(pg_skip_exempt=True))\
                        ._compute_price(product, quantity, uom, date, currency=currency)
                    return price + exempt
        return super()._compute_price(product, quantity, uom, date, currency=currency)
