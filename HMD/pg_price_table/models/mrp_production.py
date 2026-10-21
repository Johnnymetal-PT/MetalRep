# -*- coding: utf-8 -*-
"""Override de `mrp.production.create` para aplicar a tabela de
aproveitamento de tecido.

Ao criar uma MO:
1. Le `price_1..10` do `product.template` do produto a fabricar.
2. Escolhe a coluna correspondente a `product_qty` (clamp em 10).
3. Encontra na BOM o movimento de "Tecido de Fornecedor"
   (deteccao por NOME LITERAL) e sobrescreve `product_uom_qty`.

Ver `__manifest__.py` para o guia completo, incluindo a nota sobre
o nome enganoso dos campos (`price_*` guarda QUANTIDADE).
"""

import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.model_create_multi
    def create(self, vals_list):
        records = self.browse()

        for vals in vals_list:
            _logger.info("Creating a new Manufacturing Order with values: %s", vals)

            product_variant = self.env['product.product'].browse(vals.get('product_id'))
            if not product_variant:
                _logger.warning("Product variant not found for product_id: %s", vals.get('product_id'))
                continue

            product_template = product_variant.product_tmpl_id
            if not product_template:
                _logger.warning("Product template not found for product_id: %s", vals.get('product_id'))
                continue

            product_qty = vals.get('product_qty') or 1.0
            _logger.info("Product quantity for the MO: %s", product_qty)

            # Quantidade de tecido por unidade conforme a coluna da tabela
            # do produto template (1 -> price_1, ..., 10 -> price_10).
            consumption_value = self._get_consumption_value(product_template, product_qty)
            _logger.info("Consumption value to be used: %s", consumption_value)

            # NOTA: product_uom_qty nao e campo direto em mrp.production. O
            # update aqui e inocuo - o efeito util esta no loop seguinte
            # sobre move_raw_ids. Mantido para nao alterar o vals existente.
            vals.update({'product_uom_qty': consumption_value})

            mo = super(MrpProduction, self).create([vals])[0]

            _logger.info("Created MO %s with stock moves: %s", mo.name, mo.move_raw_ids)

            # HARDCODED: identifica o movimento de tecido pelo NOME EXATO
            # do produto. Se a HMD renomear o produto "Tecido de
            # Fornecedor", este filtro deixa de aplicar - alterar aqui.
            for move in mo.move_raw_ids:
                _logger.info("Move: %s, Product: %s, Para Consumir: %s", move.name, move.product_id.name, move.product_uom_qty)

                if move.product_id.name == 'Tecido de Fornecedor':
                    tecido_val = self._get_consumption_value(product_template, product_qty)
                    move.product_uom_qty = tecido_val
                    _logger.info("'Tecido de Fornecedor' quantity overridden to: %s", tecido_val)

            records |= mo

        return records

    def _get_consumption_value(self, product_template, product_qty):
        """Devolve o valor da tabela `price_*` correspondente a `product_qty`.

        Clamp duro em 10 (mais de 10 unidades usa sempre `price_10`).
        Quantidades < 1 caem na coluna 1 (defensivo).
        """
        _logger.info("Fetching consumption values for product: %s", product_template.name)

        consumption_table = [
            product_template.price_1, product_template.price_2, product_template.price_3,
            product_template.price_4, product_template.price_5, product_template.price_6,
            product_template.price_7, product_template.price_8, product_template.price_9,
            product_template.price_10
        ]
        _logger.info("Consumption table: %s", consumption_table)

        if not product_qty or product_qty < 1:
            _logger.warning("Invalid quantity (%s), defaulting to first value", product_qty)
            return consumption_table[0]

        # Clamp: qty > 10 fica no ultimo valor (curva ja estabilizada).
        index = min(int(product_qty) - 1, len(consumption_table) - 1)
        selected = consumption_table[index]
        _logger.info("Selected value from row %s: %s", index + 1, selected)
        return selected
