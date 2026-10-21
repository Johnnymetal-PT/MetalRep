# -*- coding: utf-8 -*-
"""Aplica a Tabela de Consumo do produto às Ordens de Fabrico.

Ver o __manifest__.py para o objetivo. Em resumo: a quantidade a consumir depende do
escalão de quantidade a produzir e vem dos campos price_1..price_10 do produto.
"""
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.model
    def create(self, vals):
        # Ao criar a MO, calcula a quantidade a consumir a partir da tabela do produto
        # e aplica-a à MO e ao movimento do componente "Tecido de Fornecedor".
        _logger.info("Creating a new Manufacturing Order with values: %s", vals)

        # Fetch the product ID (variant) and its associated product template (main product)
        product_variant = self.env['product.product'].browse(vals.get('product_id'))
        if not product_variant:
            _logger.warning("Product variant not found for product_id: %s", vals.get('product_id'))
        else:
            _logger.info("Product variant found: %s", product_variant)

        product_template = product_variant.product_tmpl_id
        if not product_template:
            _logger.warning("Product template not found for product_id: %s", vals.get('product_id'))
        else:
            _logger.info("Product template found: %s", product_template)

        product_qty = vals.get('product_qty')
        _logger.info("Product quantity for the MO: %s", product_qty)

        # Fetch the correct consumption value based on the product template (main product) and product_qty
        consumption_value = self._get_consumption_value(product_template, product_qty)
        _logger.info("Consumption value to be used: %s", consumption_value)

        # Update the manufacturing order with the fetched consumption value for 'Para Consumir'
        vals.update({'product_uom_qty': consumption_value})
        _logger.info("Updated Manufacturing Order values with consumption value: %s", vals)

        # Proceed with creating the MO
        mo = super(MrpProduction, self).create(vals)

        # Log the stock moves associated with the manufacturing order
        _logger.info("Stock Moves associated with this MO: %s", mo.move_raw_ids)
        for move in mo.move_raw_ids:
            _logger.info("Move: %s, Product: %s, Planned Quantity (Para Consumir): %s", move, move.product_id, move.product_uom_qty)

            # Special check for 'Tecido de Fornecedor' and use the main product's consumption table
            if move.product_id.name == 'Tecido de Fornecedor':
                _logger.info("Found 'Tecido de Fornecedor' stock move with Planned Quantity: %s", move.product_uom_qty)

                # Use the main product's consumption value for 'Tecido de Fornecedor'
                _logger.info("Fetching consumption value from the main product table.")
                tecido_consumption_value = self._get_consumption_value(product_template, product_qty)
                _logger.info("Overriding 'Tecido de Fornecedor' Planned Quantity with: %s", tecido_consumption_value)

                # Override the stock move's product_uom_qty with the main product's consumption value
                move.product_uom_qty = tecido_consumption_value
                _logger.info("'Tecido de Fornecedor' stock move updated to Planned Quantity: %s", move.product_uom_qty)

        return mo

    def _get_consumption_value(self, product_template, product_qty):
        """Devolve a quantidade a consumir para o escalão correspondente a `product_qty`.

        Lê a Tabela de Consumo (price_1..price_10) do produto e escolhe o valor do
        escalão certo; acima de 10 unidades usa o último valor da tabela.
        """
        _logger.info("Fetching consumption values for product template: %s", product_template)

        # Os 10 valores da Tabela de Consumo, por ordem de escalão (índice 0 = escalão 1).
        consumption_table = [
            product_template.price_1, product_template.price_2, product_template.price_3,
            product_template.price_4, product_template.price_5, product_template.price_6,
            product_template.price_7, product_template.price_8, product_template.price_9,
            product_template.price_10
        ]
        _logger.info("Consumption table values: %s", consumption_table)

        # Logic to determine which consumption value to pick based on the total product_qty
        if product_qty <= 1:
            return consumption_table[0]  # Use the value in Price 1 field
        elif product_qty <= 2:
            return consumption_table[1]
        elif product_qty <= 3:
            return consumption_table[2]
        elif product_qty <= 4:
            return consumption_table[3]
        elif product_qty <= 5:
            return consumption_table[4]
        elif product_qty <= 6:
            return consumption_table[5]
        elif product_qty <= 7:
            return consumption_table[6]
        elif product_qty <= 8:
            return consumption_table[7]
        elif product_qty <= 9:
            return consumption_table[8]
        elif product_qty <= 10:
            return consumption_table[9]
        else:
            return consumption_table[-1]  # Default to the last value if product_qty exceeds the range

