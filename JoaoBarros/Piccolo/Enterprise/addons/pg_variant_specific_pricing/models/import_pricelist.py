import base64
import pandas as pd
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def action_import_pricelist(self):
        view_id = self.env.ref('pg_variant_specific_pricing.pricelist_import_wizard_form').id
        return {
            'name': _('Import Pricelist'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'pricelist.import.wizard',
            'views': [(view_id, 'form')],
            'target': 'new',
        }

class ProductProduct(models.Model):
    _inherit = 'product.product'

    lst_price = fields.Float('Sales Price', compute=False, store=True)

    @api.model
    def create(self, vals):
        if 'lst_price' in vals:
            vals['lst_price'] = vals.get('lst_price')
            _logger.info(f"Creating product with price: {vals['lst_price']}")
        return super(ProductProduct, self).create(vals)

    def write(self, vals):
        if 'lst_price' in vals:
            _logger.info(f"Updating product {self.id} with price: {vals['lst_price']}")
            vals['lst_price'] = vals.get('lst_price')
        return super(ProductProduct, self).write(vals)

    @api.model
    def _get_combination_info(self, combination, product_id, add_qty=1, pricelist=None, parent_combination=None, **kwargs):
        _logger.info(f"Fetching combination info for product ID: {product_id}")
        
        # Call the super method to get the initial combination info
        combination_info = super(ProductTemplate, self)._get_combination_info(
            combination, product_id, add_qty, pricelist, parent_combination, **kwargs)
        
        if product_id:
            product = self.env['product.product'].browse(product_id)
            if product:
                _logger.info(f"Product {product.display_name} has price: {product.lst_price}")
                
                # Force lst_price to be used for both price and price_without_discount
                combination_info['price'] = product.lst_price
                combination_info['price_without_discount'] = product.lst_price
                
                # Set price_extra to 0 to neutralize any impact from other pricing logic
                combination_info['price_extra'] = 0.0
                
                # Reconfirm and log final values
                _logger.info(f"Final combination info using lst_price: {combination_info}")

        # Additional logging to ensure we're capturing the right combination info
        _logger.info(f"Returning combination info: {combination_info}")
        
        return combination_info


    def action_import_pricelist(self):
        view_id = self.env.ref('pg_variant_specific_pricing.pricelist_import_wizard_form').id
        return {
            'name': _('Import Pricelist'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'pricelist.import.wizard',
            'views': [(view_id, 'form')],
            'target': 'new',
        }

class PricelistImportWizard(models.TransientModel):
    _name = 'pricelist.import.wizard'
    _description = 'Wizard to Import Pricelist'

    file = fields.Binary('File', required=True)
    filename = fields.Char('Filename')

    def import_pricelist(self):
        if self.file:
            file_content = base64.b64decode(self.file)
            df = pd.read_excel(file_content)

            for index, row in df.iterrows():
                _logger.info(f"Processing row {index + 1}: {row.to_dict()}")
                
                external_id = row['id']
                res_model_res_id = self.env['ir.model.data']._xmlid_to_res_model_res_id(external_id)
                if res_model_res_id:
                    model, res_id = res_model_res_id
                    if model == 'product.product':
                        product_variant = self.env[model].browse(res_id)

                        _logger.info(f"Found variant: {product_variant.display_name} (ID: {product_variant.id}) - Updating price to {row['lst_price']}")
                        product_variant.sudo().write({
                            'lst_price': row['lst_price'],
                            'price_extra': 0.0,  # neutralize any price_extra
                        })

                        _logger.info(f"Updated variant {product_variant.display_name} (ID: {product_variant.id}) with price {row['lst_price']}")

        return {'type': 'ir.actions.act_window_close'}

