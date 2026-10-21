"""Wizard para importar pricelists+items de um Excel.

Cada linha do Excel cria uma pricelist nova + items para as
variantes indicadas. NAO e idempotente - re-import duplica.

Formato esperado (HARDCODED nomes de coluna):
- ``name`` (nome da pricelist)
- ``item_ids/product_tmpl_id`` (external id ou id do template)
- ``item_ids/product_id`` (CSV de ids de product.attribute.value)
- ``item_ids/fixed_price`` (preco)
"""
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
        if not self.file:
            return

        try:
            # BytesIO evita escrever a tempfile (mais rapido que tmp).
            file_content = base64.b64decode(self.file)
            df = pd.read_excel(BytesIO(file_content))

            for index, row in df.iterrows():
                # Cria pricelist nova - NAO procura existentes (re-import
                # duplica nomes; aceitar ou converter para search-then-create).
                pricelist = self.env['product.pricelist'].create({
                    'name': row['name'],
                    'currency_id': self.env.user.company_id.currency_id.id,
                    'active': True,
                })

                # External id no formato "modulo.product_template_15_abc"
                # -> split por '_' pega no ultimo "abc" mas converte com int.
                # Em pratica o ultimo elemento e numerico (id Odoo).
                product_template_id = self.env['product.template'].search(
                    [('id', '=', int(row['item_ids/product_tmpl_id'].split('_')[-1]))],
                )
                if not product_template_id:
                    continue

                # CSV de variant ids separados por ','. Cada um e
                # tratado como ``product.attribute.value`` para
                # localizar a variante pelo combination.
                variant_ids = row['item_ids/product_id'].split(',')
                for variant_id in variant_ids:
                    variant_record = self.env['product.product'].search([
                        ('product_tmpl_id', '=', product_template_id.id),
                        ('product_template_variant_value_ids', 'in', [int(variant_id.split('_')[-1])]),
                    ], limit=1)

                    if not variant_record:
                        continue

                    self.env['product.pricelist.item'].create({
                        'pricelist_id': pricelist.id,
                        'product_tmpl_id': product_template_id.id,
                        'product_id': variant_record.id,
                        'fixed_price': row['item_ids/fixed_price'],
                    })

            return {'type': 'ir.actions.act_window_close'}

        except Exception as e:
            _logger.error("An error occurred during pricelist import: %s", e)
            raise


class Pricelist(models.Model):
    _inherit = 'product.pricelist'

    def action_import_pricelist(self):
        """Botao "Importar Pricelist" - abre o wizard."""
        view_id = self.env.ref('pg_upload_pricelists.pricelist_import_wizard_form').id
        return {
            'name': _('Import Pricelist'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'pricelist.import.wizard',
            'views': [(view_id, 'form')],
            'target': 'new',
        }
