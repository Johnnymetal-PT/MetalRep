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

            # Get the correct consumption value
            consumption_value = self._get_consumption_value(product_template, product_qty)
            _logger.info("Consumption value to be used: %s", consumption_value)

            # Update the vals with calculated quantity
            vals.update({'product_uom_qty': consumption_value})
            _logger.info("Updated vals with product_uom_qty: %s", vals)

            # Create the MO record
            mo = super(MrpProduction, self).create([vals])[0]

            _logger.info("Created MO %s with stock moves: %s", mo.name, mo.move_raw_ids)

            for move in mo.move_raw_ids:
                _logger.info("Move: %s, Product: %s, Para Consumir: %s", move.name, move.product_id.name, move.product_uom_qty)

                if move.product_id.name == 'Tecido de Fornecedor':
                    tecido_val = self._get_consumption_value(product_template, product_qty)
                    move.product_uom_qty = tecido_val
                    _logger.info("'Tecido de Fornecedor' quantity overridden to: %s", tecido_val)

            records |= mo

        return records

    def _get_consumption_value(self, product_template, product_qty):
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

        index = min(int(product_qty) - 1, len(consumption_table) - 1)
        selected = consumption_table[index]
        _logger.info("Selected value from row %s: %s", index + 1, selected)
        return selected
