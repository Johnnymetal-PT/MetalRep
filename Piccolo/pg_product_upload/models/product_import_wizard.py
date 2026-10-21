"""Wizard de import de produtos+variantes a partir de Excel.

Formato do Excel (HARDCODED - validar antes de importar):
- **Linha 1**: nome do atributo, com merge horizontal sobre as
  colunas das suas variantes. ``Atributos`` e ``Variantes`` sao
  reservadas (saltadas).
- **Linha 2**: nome da variante por coluna.
- **Linhas 3+**: coluna 0 = nome do produto; colunas seguintes =
  ``price_extra`` (numerico) **ou** descricao textual para
  ``custom.product.attribute``.

ATENCAO: re-importar elimina os ``custom.product.attribute`` dos
produtos da importacao (unlink antes de re-popular).
"""
import base64
import tempfile
import pandas as pd
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ProductImportWizard(models.TransientModel):
    _name = 'product.import.wizard'
    _description = 'Product Import Wizard'

    file = fields.Binary('Ficheiro', required=True)
    filename = fields.Char('Nome', required=True)

    def action_import(self):
        if not self.file or not self.filename:
            raise UserError('Please upload a file.')

        # Persistir o binary num tempfile para o pandas conseguir abrir
        # com seek/tell - BytesIO tambem funcionava mas mantemos
        # ficheiro para diagnostico se algo falhar.
        try:
            file_content = base64.b64decode(self.file)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
                tmp_file.write(file_content)
                tmp_file_path = tmp_file.name
        except Exception as e:
            raise UserError(f'Failed to process file: {str(e)}')

        self.env['product.import'].import_file(tmp_file_path)


class ProductImport(models.TransientModel):
    _name = 'product.import'
    _description = 'Import Product'

    @api.model
    def import_file(self, file_path):
        df = pd.read_excel(file_path, sheet_name=0)

        # Linha 1: atributos. ffill propaga o nome do atributo nas
        # cells que estavam em merge horizontal (ficam NaN no pandas).
        # NOTA: ffill(method='ffill') esta deprecated em pandas 2.x.
        attribute_categories = df.iloc[0].fillna(method='ffill').to_list()

        # Linha 2: nomes de variante por coluna.
        variants = df.iloc[1].to_list()

        # Construir mapeamento attr -> [(col_index, variant_name), ...]
        # Saltar duas primeiras colunas (Atributos e Variantes - reservadas).
        attr_variant_map = {}
        for col_index, (attr, var) in enumerate(zip(attribute_categories, variants)):
            if attr == "Atributos" or var == "Variantes":
                continue
            attr_upper = str(attr).upper()
            if attr_upper in attr_variant_map:
                attr_variant_map[attr_upper].append((col_index, var))
            else:
                attr_variant_map[attr_upper] = [(col_index, var)]

        # ---- Criar atributos e valores se nao existirem ----
        for attr, col_indices in attr_variant_map.items():
            for col_index, variant in col_indices:
                if pd.isna(variant) or variant == '':
                    continue

                attribute_id = self.env['product.attribute'].search([('name', '=', attr)], limit=1)
                if not attribute_id:
                    # display_type=select + unavailable_value_view_type=hide
                    # para esconder variantes nao disponiveis no /shop.
                    attribute_id = self.env['product.attribute'].create({
                        'name': attr,
                        'display_type': 'select',
                        'unavailable_value_view_type': 'hide',
                    })

                existing_value = self.env['product.attribute.value'].search(
                    [('name', '=', str(variant)), ('attribute_id', '=', attribute_id.id)], limit=1,
                )
                if not existing_value:
                    try:
                        self.env['product.attribute.value'].create({
                            'name': str(variant),
                            'attribute_id': attribute_id.id,
                        })
                    except Exception as e:
                        _logger.warning("Failed to create variant '%s' for '%s': %s", variant, attr, e)

        # ---- Apagar custom attributes dos produtos a re-importar ----
        # Importante: a re-importacao limpa apenas os custom.product.attribute
        # dos produtos presentes neste ficheiro - nao toca em produtos
        # nao incluidos.
        imported_product_names = df.iloc[2:, 0].dropna().apply(str.strip).tolist()
        imported_product_ids = self.env['product.template'].search([('name', 'in', imported_product_names)])

        try:
            self.env['custom.product.attribute'].search(
                [('product_id', 'in', imported_product_ids.ids)],
            ).unlink()
        except Exception as e:
            _logger.warning("Failed to delete custom product attributes: %s", e)

        # ---- Aplicar variantes a cada produto ----
        for index, row in df.iterrows():
            if index < 2:
                # Skip cabecalho (linhas 0 e 1, ja processadas).
                continue
            if pd.isna(row[0]):
                continue

            if isinstance(row[0], str):
                product_name = row[0].strip()
            else:
                product_name = str(row[0])

            # Match exato (case-sensitive). Produto novo se nao existir.
            product = self.env['product.product'].search([('name', '=', product_name)], limit=1)
            if not product:
                product_template = self.env['product.template'].create({
                    'name': product_name,
                    # Por defeito publica no website - decisao Piccolo
                    # para minimizar passos pos-import.
                    'website_published': True,
                    'type': 'product',
                })
                product = self.env['product.product'].search([('product_tmpl_id', '=', product_template.id)], limit=1)

            if not product:
                continue

            index_custom_attib = 0
            for attr, col_indices in attr_variant_map.items():
                attribute_id = self.env['product.attribute'].search([('name', '=', attr)], limit=1)
                if not attribute_id:
                    continue

                for col_index, variant in col_indices:
                    if pd.isna(row[col_index]) or row[col_index] == '':
                        continue

                    # Valor TEXTUAL (nao numerico) -> custom attribute,
                    # nao variante standard. Heuristica simples: se nao
                    # for int/float, e descricao textual.
                    if not pd.isna(row[col_index]) and not isinstance(row[col_index], (int, float)) and row[col_index] != '':
                        index_custom_attib += 1
                        existing_custom_attr = self.env['custom.product.attribute'].search([
                            ('name', '=', attr),
                            ('product_id', '=', product.product_tmpl_id.id),
                        ], limit=1)

                        if existing_custom_attr:
                            existing_custom_attr.write({
                                'description': str(variant),
                                'sequence': index_custom_attib,
                            })
                        else:
                            self.env['custom.product.attribute'].create({
                                'name': attr,
                                'product_id': product.product_tmpl_id.id,
                                'description': str(variant),
                                'sequence': index_custom_attib,
                            })
                        continue

                    # Valor NUMERICO -> ``price_extra`` no PTAV.
                    value_id = self.env['product.attribute.value'].search(
                        [('name', '=', str(variant)), ('attribute_id', '=', attribute_id.id)], limit=1,
                    )

                    if not value_id:
                        value_id = self.env['product.attribute.value'].create({
                            'name': str(variant),
                            'attribute_id': attribute_id.id,
                        })

                    # Garantir attribute_line no template (uma por atributo).
                    existing_line = self.env['product.template.attribute.line'].search([
                        ('product_tmpl_id', '=', product.product_tmpl_id.id),
                        ('attribute_id', '=', attribute_id.id),
                    ])
                    if existing_line:
                        if value_id.id not in existing_line.value_ids.ids:
                            existing_line.write({'value_ids': [(4, value_id.id)]})
                    else:
                        product.write({'attribute_line_ids': [
                            (0, 0, {'attribute_id': attribute_id.id, 'value_ids': [(4, value_id.id)]})
                        ]})

                    # Atualizar price_extra no PTAV.
                    # NOTA: o search NAO filtra por template - se o
                    # valor for partilhado por varios templates, escreve
                    # no primeiro PTAV (potencial bug em catalogos grandes).
                    line_value = self.env['product.template.attribute.value'].search([
                        ('product_attribute_value_id', '=', value_id.id),
                    ], limit=1)
                    if line_value:
                        line_value.write({'price_extra': row[col_index]})
                    else:
                        self.env['product.template.attribute.value'].create({
                            'product_attribute_value_id': value_id.id,
                            'price_extra': row[col_index],
                        })
