from odoo import models, fields
import base64
import tempfile
import pandas as pd

class PtavPriceImportWizard(models.TransientModel):
    _name = 'ptav.price.import.wizard'
    _description = 'Import PTAV Price Extra from Excel'

    file = fields.Binary(string="Excel File", required=True)
    filename = fields.Char(string="Filename")

    def action_import(self):
        if not self.file:
            raise UserError("Please upload an Excel file.")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp.write(base64.b64decode(self.file))
            tmp.flush()
            df = pd.read_excel(tmp.name)

        updated = 0
        skipped = 0

        for index, row in df.iterrows():
            ptav_id = row.get('ID')
            price_extra = row.get('Value Price Extra')

            if pd.isna(ptav_id) or pd.isna(price_extra):
                skipped += 1
                continue

            ptav = self.env['product.template.attribute.value'].sudo().browse(int(ptav_id))
            if ptav.exists():
                ptav.write({'price_extra': float(price_extra)})
                updated += 1
            else:
                skipped += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Import Complete',
                'message': f'{updated} records updated. {skipped} skipped.',
                'type': 'success',
                'sticky': False,
            }
        }
