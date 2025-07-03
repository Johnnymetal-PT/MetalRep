"""
from odoo import models, fields, api
from odoo.exceptions import UserError

class ProductImportWizard(models.TransientModel):
    _name = 'product.import.wizard'
    _description = 'Product Import Wizard'

    file = fields.Binary('Ficheiro')
    filename = fields.Char('Nome')

    def action_import(self):
        if not self.file:
            raise UserError('Please upload a file.')
        file_path = "c:/temp/{}".format(self.filename)
        with open(file_path, "wb") as f:
            f.write(self.file.decode("base64"))
        self.env['product.import'].import_file(file_path)
"""
