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

        # Save the file to a temporary location
        try:
            file_content = base64.b64decode(self.file)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
                tmp_file.write(file_content)
                tmp_file_path = tmp_file.name
        except Exception as e:
            raise UserError(f'Failed to process file: {str(e)}')

        # Use the temporary file path to import the file
        self.env['product.import'].import_file(tmp_file_path)

class ProductImport(models.TransientModel):
    _name = 'product.import'
    _description = 'Import Product'

    @api.model
    def import_file(self, file_path):
        #try:
            # Read the first sheet of the Excel file
            df = pd.read_excel(file_path, sheet_name=0)

            # Extract attribute categories from the first row (considering merged cells)
            attribute_categories = df.iloc[0].fillna(method='ffill').to_list()
            _logger.info(f"Raw attribute categories extracted from the first row: {attribute_categories}")

            # Extract variants from the second row
            variants = df.iloc[1].to_list()
            _logger.info(f"Variants extracted from the second row: {variants}")

            # Create a mapping of column indexes to attribute names and variants
            attr_variant_map = {}
            for col_index, (attr, var) in enumerate(zip(attribute_categories, variants)):
                if attr == "Atributos" or var == "Variantes":
                    continue  # Skip the "Atributos" and "Variantes" columns
                attr_upper = str(attr).upper()
                if attr_upper in attr_variant_map:
                    attr_variant_map[attr_upper].append((col_index, var))
                else:
                    attr_variant_map[attr_upper] = [(col_index, var)]

            # Log the attribute-variant mapping
            _logger.info(f"Attribute-variant mapping: {attr_variant_map}")

            # Create attributes and variants
            for attr, col_indices in attr_variant_map.items():

                # Add variants to the attribute
                for col_index, variant in col_indices:
                    if pd.isna(variant) or variant == '':
                        _logger.warning(f"Skipped empty variant for attribute '{attr}'")
                        continue

                    # Check if the attribute already exists
                    attribute_id = self.env['product.attribute'].search([('name', '=', attr)], limit=1)
                    if not attribute_id:
                        attribute_id = self.env['product.attribute'].create({'name': attr})
                        _logger.info(f"Attribute created: {attr}")
                    else:
                        _logger.info(f"Attribute already exists: {attr}")

                    _logger.info(f"Checking if variant '{variant}' exists for attribute '{attr}'")

                    existing_value = self.env['product.attribute.value'].search(
                        [('name', '=', str(variant)), ('attribute_id', '=', attribute_id.id)], limit=1)
                    if not existing_value:
                        try:
                            _logger.info(f"Creating variant '{variant}' for attribute '{attr}'")
                            self.env['product.attribute.value'].create({
                                'name': str(variant),
                                'attribute_id': attribute_id.id
                            })
                        except Exception as e:
                            _logger.warning(f"Failed to create variant '{variant}' for attribute '{attr}': {e}")
                    else:
                        _logger.info(f"Variant '{variant}' already exists for attribute '{attr}'")

            # Delete existing custom attributes for the product
            try:
                self.env['custom.product.attribute'].search([]).unlink()
            except Exception as e: 
                {}


            # Apply variants to products
            for index, row in df.iterrows():
                if index < 2:
                    continue
                if pd.isna(row[0]):
                    continue
                
                # Ensure row[0] is a string before calling strip
                if isinstance(row[0], str):
                    product_name = row[0].strip()
                else:
                    product_name = str(row[0])

                product = self.env['product.product'].search([('name', 'ilike', product_name)], limit=1)
                if not product:
                    product = self.env['product.template'].create({
                        'name': product_name,
                        'website_published': True,
                        'type': 'product'
                    })
                    # _logger.warning(f"Product not found: {product_name}")
                    # continue

                product = self.env['product.product'].search([('name', 'ilike', product_name)], limit=1)
                """
                try:
                    self.env['product.template.attribute.line'].search([('product_tmpl_id', '=', product.product_tmpl_id.id)]).unlink()
                except Exception as e: 
                    {}
                """

                index_custom_attib = 0
                for attr, col_indices in attr_variant_map.items():
                    attribute_id = self.env['product.attribute'].search([('name', '=', attr)], limit=1)
                    if not attribute_id:
                        _logger.warning(f"Attribute not found: {attr}")
                        continue

                    for col_index, variant in col_indices:
                        if pd.isna(row[col_index]) or row[col_index] == '':
                            _logger.warning(f"Skipped empty variant value for product '{product_name}', attribute '{attr}'")
                            continue

                        if not pd.isna(row[col_index]) and not isinstance(row[col_index], (int, float)) and row[col_index] != '':
                            # Handle non-numeric values as custom attributes
                            index_custom_attib += 1
                            custom_attr_id = self.env['custom.product.attribute'].create({
                                'name': attr,
                                'product_id': product.product_tmpl_id.id,
                                'description': str(variant),
                                'sequence': index_custom_attib  # Assuming sequence is based on row index
                            })
                            _logger.info(f"Custom attribute created: {custom_attr_id} {custom_attr_id.name} {custom_attr_id.product_id} {custom_attr_id.description} {custom_attr_id.sequence}")
                            continue
                        """
                        value_id = self.env['product.attribute.value'].search(
                            [('name', '=', str(variant)), ('attribute_id', '=', attribute_id.id)], limit=1)
                        
                        if value_id:
                            try:
                                value_id.unlink()
                            except Exception as e: 
                                {}
                        """
                        value_id = self.env['product.attribute.value'].search(
                            [('name', '=', str(variant)), ('attribute_id', '=', attribute_id.id)], limit=1)

                        if not value_id:
                            value_id = self.env['product.attribute.value'].create({
                                'name': str(variant),
                                'attribute_id': attribute_id.id,
                            })
                        existing_line = self.env['product.template.attribute.line'].search([
                            ('product_tmpl_id', '=', product.product_tmpl_id.id),
                            ('attribute_id', '=', attribute_id.id)
                        ])
                        if existing_line:
                            if value_id.id not in existing_line.value_ids.ids:
                                existing_line.write({'value_ids': [(4, value_id.id)]})
                        else:
                            product.write({'attribute_line_ids': [
                                (0, 0, {'attribute_id': attribute_id.id, 'value_ids': [(4, value_id.id)]})]})
                        _logger.info(f"Variant '{variant}' applied to product '{product_name}'")

                        line_value = self.env['product.template.attribute.value'].search([
                            ('product_attribute_value_id', '=', value_id.id)
                        ], limit=1)
                        if line_value:
                            line_value.write({'price_extra': row[col_index]})
                        else:
                            self.env['product.template.attribute.value'].create({
                                'product_attribute_value_id': value_id.id,
                                'price_extra': row[col_index]
                            })


        #except Exception as e:
        #    _logger.error(f"Failed to import file: {str(e)}")
        #    raise UserError(f"Failed to import file: {str(e)}")



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

        # Save the file to a temporary location
        try:
            file_content = base64.b64decode(self.file)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
                tmp_file.write(file_content)
                tmp_file_path = tmp_file.name
        except Exception as e:
            raise UserError(f'Failed to process file: {str(e)}')

        # Use the temporary file path to import the file
        self.env['product.import'].import_file(tmp_file_path)

class ProductImport(models.TransientModel):
    _name = 'product.import'
    _description = 'Import Product'

    @api.model
    def import_file(self, file_path):
        try:
            # Read the first sheet of the Excel file
            df = pd.read_excel(file_path, sheet_name=0)

            # Extract attribute categories from the first row (considering merged cells)
            attribute_categories = df.iloc[0].fillna(method='ffill').to_list()
            _logger.info(f"Raw attribute categories extracted from the first row: {attribute_categories}")

            # Extract variants from the second row
            variants = df.iloc[1].to_list()
            _logger.info(f"Variants extracted from the second row: {variants}")

            # Create a mapping of column indexes to attribute names and variants
            attr_variant_map = {}
            for col_index, (attr, var) in enumerate(zip(attribute_categories, variants)):
                if attr == "Atributos" or var == "Variantes":
                    continue  # Skip the "Atributos" and "Variantes" columns
                attr_upper = str(attr).upper()
                if attr_upper in attr_variant_map:
                    attr_variant_map[attr_upper].append((col_index, var))
                else:
                    attr_variant_map[attr_upper] = [(col_index, var)]

            # Log the attribute-variant mapping
            _logger.info(f"Attribute-variant mapping: {attr_variant_map}")

            # Create attributes and variants
            for attr, col_indices in attr_variant_map.items():
                # Check if the attribute already exists
                attribute_id = self.env['product.attribute'].search([('name', '=', attr)], limit=1)
                if not attribute_id:
                    attribute_id = self.env['product.attribute'].create({'name': attr})
                    _logger.info(f"Attribute created: {attr}")
                else:
                    _logger.info(f"Attribute already exists: {attr}")

                # Add variants to the attribute
                for col_index, variant in col_indices:
                    if pd.isna(variant) or variant == '':
                        _logger.warning(f"Skipped empty variant for attribute '{attr}'")
                        continue

                    _logger.info(f"Checking if variant '{variant}' exists for attribute '{attr}'")
                    existing_value = self.env['product.attribute.value'].search(
                        [('name', '=', str(variant)), ('attribute_id', '=', attribute_id.id)], limit=1)
                    if not existing_value:
                        try:
                            _logger.info(f"Creating variant '{variant}' for attribute '{attr}'")
                            self.env['product.attribute.value'].create({
                                'name': str(variant),
                                'attribute_id': attribute_id.id
                            })
                        except Exception as e:
                            _logger.warning(f"Failed to create variant '{variant}' for attribute '{attr}': {e}")
                    else:
                        _logger.info(f"Variant '{variant}' already exists for attribute '{attr}'")

            # Apply variants to products
            for index, row in df.iterrows():
                if index < 2:
                    continue
                if pd.isna(row[0]):
                    continue
                product_name = row[0].strip().upper()
                product = self.env['product.product'].search([('name', 'ilike', product_name)], limit=1)
                if not product:
                    _logger.warning(f"Product not found: {product_name}")
                    continue

                for attr, col_indices in attr_variant_map.items():
                    attribute_id = self.env['product.attribute'].search([('name', '=', attr)], limit=1)
                    if not attribute_id:
                        _logger.warning(f"Attribute not found: {attr}")
                        continue

                    for col_index, variant in col_indices:
                        if pd.isna(row[col_index]) or row[col_index] == '':
                            _logger.warning(f"Skipped empty variant value for product '{product_name}', attribute '{attr}'")
                            continue

                        value_id = self.env['product.attribute.value'].search(
                            [('name', '=', str(variant)), ('attribute_id', '=', attribute_id.id)], limit=1)
                        if not value_id:
                            value_id = self.env['product.attribute.value'].create({
                                'name': str(variant),
                                'attribute_id': attribute_id.id
                            })
                        existing_line = self.env['product.template.attribute.line'].search([
                            ('product_tmpl_id', '=', product.product_tmpl_id.id),
                            ('attribute_id', '=', attribute_id.id)
                        ])
                        if existing_line:
                            if value_id.id not in existing_line.value_ids.ids:
                                existing_line.write({'value_ids': [(4, value_id.id)]})
                        else:
                            product.write({'attribute_line_ids': [
                                (0, 0, {'attribute_id': attribute_id.id, 'value_ids': [(4, value_id.id)]})]})
                        _logger.info(f"Variant '{variant}' applied to product '{product_name}'")

        except Exception as e:
            _logger.error(f"Failed to import file: {str(e)}")
            raise UserError(f"Failed to import file: {str(e)}")
"""