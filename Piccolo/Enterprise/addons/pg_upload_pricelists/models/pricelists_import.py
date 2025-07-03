from io import BytesIO
from odoo import models, fields, api, _
import base64
import pandas as pd
import logging

_logger = logging.getLogger(__name__)

class PricelistImportWizard(models.TransientModel):
    _name = 'pricelist.import.wizard'
    _description = 'Pricelist Import Wizard'

    file = fields.Binary('File', required=True)
    filename = fields.Char('Filename')

    def import_pricelist(self):
        _logger.info("Starting the import_pricelist method.")  # Initial log to confirm execution

        if not self.file:
            _logger.warning("No file uploaded. Exiting method.")
            return

        try:
            # Wrap the file content in BytesIO to avoid the FutureWarning
            file_content = base64.b64decode(self.file)
            df = pd.read_excel(BytesIO(file_content))

            # Loop through each row in the Excel file
            for index, row in df.iterrows():
                _logger.info(f"Processing row {index + 1}: {row.to_dict()}")

                # Create a new pricelist for each unique 'name'
                pricelist = self.env['product.pricelist'].create({
                    'name': row['name'],
                    'currency_id': self.env.user.company_id.currency_id.id,  # Default currency of the company
                    'active': True,
                })
                _logger.info(f"Created new pricelist: {pricelist.name} (ID: {pricelist.id})")

                # Search for the product template using the provided template ID
                product_template_id = self.env['product.template'].search([('id', '=', int(row['item_ids/product_tmpl_id'].split('_')[-1]))])
                if not product_template_id:
                    _logger.warning(f"Product template with ID {row['item_ids/product_tmpl_id']} not found. Skipping row.")
                    continue

                # Splitting and processing each variant ID
                variant_ids = row['item_ids/product_id'].split(',')
                for variant_id in variant_ids:
                    variant_record = self.env['product.product'].search([
                        ('product_tmpl_id', '=', product_template_id.id),
                        ('product_template_variant_value_ids', 'in', [int(variant_id.split('_')[-1])]),
                    ], limit=1)

                    if not variant_record:
                        _logger.warning(f"Variant with ID {variant_id} not found. Skipping this variant.")
                        continue

                    # Create pricelist item for the variant
                    pricelist_item = self.env['product.pricelist.item'].create({
                        'pricelist_id': pricelist.id,
                        'product_tmpl_id': product_template_id.id,
                        'product_id': variant_record.id,
                        'fixed_price': row['item_ids/fixed_price'],
                    })
                    _logger.info(f"Created pricelist item for variant {variant_record.name} with price {row['item_ids/fixed_price']}")

            _logger.info("Completed processing all rows.")
            return {'type': 'ir.actions.act_window_close'}

        except Exception as e:
            _logger.error(f"An error occurred during pricelist import: {e}")
            raise

class Pricelist(models.Model):
    _inherit = 'product.pricelist'

    def action_import_pricelist(self):
        _logger.info("Button action_import_pricelist triggered.")
        view_id = self.env.ref('pg_upload_pricelists.pricelist_import_wizard_form').id
        return {
            'name': _('Import Pricelist'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'pricelist.import.wizard',
            'views': [(view_id, 'form')],
            'target': 'new',
        }

