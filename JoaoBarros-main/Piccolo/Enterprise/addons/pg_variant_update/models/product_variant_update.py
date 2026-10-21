# models/product_variant_update_wizard.py

from odoo import models, fields, api
import base64
import pandas as pd
from io import BytesIO

class ProductVariantUpdateWizard(models.TransientModel):
    _name = 'product.variant.update.wizard'
    _description = 'Wizard to Update Product Variants from Excel'

    file = fields.Binary(string="Upload Excel File", required=True)
    file_name = fields.Char(string="File Name")

    def action_update_variants(self):
        """ This method is called when the user clicks the Update button on the wizard """
        if self.file:
            # Decode the uploaded file
            file_content = base64.b64decode(self.file)
            # Load the file into a Pandas DataFrame
            excel_data = pd.read_excel(BytesIO(file_content))

            # Update product variants based on the Excel file
            for _, row in excel_data.iterrows():
                product = self.env['product.product'].search([
                    ('name', '=', row['Nome']),
                    ('attribute_value_ids.name', '=', row['Valores de Variante'])
                ], limit=1)

                if product:
                    product.write({
                        'volume': row['Volume'],
                        'quantidade_volume': row['Quantidade Volume']
                    })

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
