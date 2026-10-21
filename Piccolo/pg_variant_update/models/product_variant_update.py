"""Wizard simples para atualizar volume/quantidade nas variantes via Excel."""
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
        """Le Excel e atualiza Volume/Quantidade Volume das variantes.

        Match: (Nome == product.product.name) AND
        (Valores de Variante == qualquer attribute_value_ids.name).
        ATENCAO: se o nome do valor for partilhado entre atributos
        diferentes, ``limit=1`` apanha o primeiro - pode atualizar
        a variante errada.
        """
        if self.file:
            file_content = base64.b64decode(self.file)
            excel_data = pd.read_excel(BytesIO(file_content))

            for _, row in excel_data.iterrows():
                product = self.env['product.product'].search([
                    ('name', '=', row['Nome']),
                    # NOTA: cross-attribute match (qualquer atributo
                    # com valor com este nome). Se "Bege" existir em
                    # dois atributos, ambiguidade silenciosa.
                    ('attribute_value_ids.name', '=', row['Valores de Variante']),
                ], limit=1)

                if product:
                    product.write({
                        'volume': row['Volume'],
                        'quantidade_volume': row['Quantidade Volume'],
                    })

        # Reload para refrescar a vista (UX simples; sem feedback
        # explicito de quantas variantes foram atualizadas).
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
