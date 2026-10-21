"""
Wizard alternativo de importacao de produtos/variantes (camada de UI).

Modulo: pg_variant_upload.
Ficheiro: pg_variant_upload\wizards\product_import_wizard.py.
Modelo principal: product.import.wizard.
"""

# CÓDIGO MORTO: todo o conteúdo deste ficheiro está comentado (string triple-quote abaixo).
# O importador ativo é models/product_import_wizard.py. Mantido apenas por histórico.
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
