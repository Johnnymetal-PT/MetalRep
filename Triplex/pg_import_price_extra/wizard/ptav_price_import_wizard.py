# -*- coding: utf-8 -*-
"""Wizard de importação em massa do `price_extra` dos valores de atributo (PTAV).

Lê um Excel com colunas `ID` e `Value Price Extra` e atualiza o suplemento de preço
de cada product.template.attribute.value. Ver o __manifest__.py para o contexto.
"""
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
        # NOTA: `UserError` não está importado neste ficheiro — esta linha levantaria
        # NameError em vez de UserError. (campo `file` é required, por isso raramente chega aqui.)
        if not self.file:
            raise UserError("Please upload an Excel file.")

        # Grava o binário num ficheiro temporário para o pandas conseguir ler o Excel.
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp.write(base64.b64decode(self.file))
            tmp.flush()
            df = pd.read_excel(tmp.name)

        updated = 0
        skipped = 0

        # Cada linha do Excel: ID do PTAV + novo valor de price_extra.
        for index, row in df.iterrows():
            ptav_id = row.get('ID')
            price_extra = row.get('Value Price Extra')

            # Ignora linhas sem ID ou sem valor (células vazias / NaN).
            if pd.isna(ptav_id) or pd.isna(price_extra):
                skipped += 1
                continue

            # sudo(): a importação pode ser corrida por utilizador sem acesso direto ao PTAV.
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
