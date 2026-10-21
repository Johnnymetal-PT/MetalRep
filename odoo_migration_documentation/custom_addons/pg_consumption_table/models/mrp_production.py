"""Mapeia o consumo de materia-prima em MOs para uma tabela fixa no produto.

Este ficheiro altera o create de mrp.production para calcular o valor de
"Para Consumir" com base nos campos price_1..price_10 do product.template.
"""

import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.model
    def create(self, vals):
        # Override estrategico:
        # o objetivo e ajustar consumos antes do motor standard gerar movimentos
        # de componentes a partir da BOM.
        _logger.info("Creating a new Manufacturing Order with values: %s", vals)

        # O consumo e guardado no template, por isso resolvemos sempre
        # product.product -> product.template no inicio do fluxo.
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

        # Campo afetado: product_uom_qty (Total Quantity no model mrp.production).
        # Neste modulo ele passa a representar a referencia de consumo calculada.
        vals.update({'product_uom_qty': consumption_value})
        _logger.info("Updated Manufacturing Order values with consumption value: %s", vals)

        # Proceed with creating the MO
        mo = super(MrpProduction, self).create(vals)

        # Log the stock moves associated with the manufacturing order
        _logger.info("Stock Moves associated with this MO: %s", mo.move_raw_ids)
        for move in mo.move_raw_ids:
            _logger.info("Move: %s, Product: %s, Planned Quantity (Para Consumir): %s", move, move.product_id, move.product_uom_qty)

            # Hardcode funcional legado: apenas este componente recebe override
            # direto na linha de movimento apos create.
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
        """
        This method returns the appropriate consumption value for any product 
        based on the total product quantity in mrp.production and the values 
        in the main product's Consumption Table.
        """
        _logger.info("Fetching consumption values for product template: %s", product_template)

        # Extract the consumption values from the product's backoffice Consumption Table
        consumption_table = [
            product_template.price_1, product_template.price_2, product_template.price_3,
            product_template.price_4, product_template.price_5, product_template.price_6,
            product_template.price_7, product_template.price_8, product_template.price_9,
            product_template.price_10
        ]
        _logger.info("Consumption table values: %s", consumption_table)

        # Tabela indexada por quantidade inteira (1..10). Acima de 10 usa a
        # ultima linha como teto funcional.
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

