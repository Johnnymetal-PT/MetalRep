import logging
import base64
import pandas as pd
from odoo import models, fields, api
from odoo.exceptions import UserError
import tempfile
import re

_logger = logging.getLogger(__name__)

class ProductImportKaveWizard(models.TransientModel):
    _name = 'product.import.kave.wizard'
    _description = 'Import Products with Kave Tag'

    file = fields.Binary('Excel File', required=True)
    filename = fields.Char('Filename')

    # Send email notification on success
    def send_success_email(self):
        """Send email using template ID 80."""
        try:
            template = self.env['mail.template'].browse(80)  # Fetch by numeric ID
            if template and template.exists():
                template.send_mail(self.id, force_send=True)
                _logger.info("Email sent successfully using template ID 80.")
            else:
                _logger.error("Email template with ID 80 not found.")
        except Exception as e:
            _logger.error(f"Error sending email notification: {e}")

    def action_import(self):
        _logger.info("Starting Kave product import process...")

        if not self.file:
            raise UserError("Please upload an Excel file.")

        _logger.info(f"File uploaded: %s", self.filename)

        # Decode the uploaded file and read it into pandas
        try:
            file_data = base64.b64decode(self.file)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
                tmp_file.write(file_data)
                tmp_file_path = tmp_file.name
            df = pd.read_excel(tmp_file_path)

            # Transform barcode column to number without decimals
            df['EAN Code'] = df['EAN Code'].apply(lambda x: str(int(x)) if pd.notna(x) else '')  # Convert to number without decimals

        except Exception as e:
            _logger.error(f"Error reading Excel file: {str(e)}")
            raise UserError(f"Error processing Excel file: {str(e)}")

        # Ensure necessary columns exist
        required_columns = [
            'Code', 'EAN Code', 'Program', 'Description', 'Stock',
            'Purchase Price', 'Discount', 'Nett Purchase Price', 'Recommended Retail Price',
            'Suggested Retail Price', 'Weight Package', 'Stock Blue', 'Stock Red',
            'Stock Grey', 'Estimated Date (dd/mm/yyyy)'
        ]
        for col in required_columns:
            if col not in df.columns:
                _logger.error(f"Missing required column: {col}")
                raise UserError(f"Missing required column: {col}")

        _logger.info("All required columns found in the Excel file.")

        # Normalize prices and discounts
        def normalize_value(value):
            if pd.isna(value):
                return 0.0  # Return 0.0 if the cell is empty
            if isinstance(value, str):
                # First, remove thousand separators ('.') and replace decimal separators (',') with '.'
                value = value.replace('.', '').replace(',', '.')

            try:
                if isinstance(value, float) or isinstance(value, str):
                    match = re.search(r'\.\d+', str(value))
                    if match:
                        decimal_digits = len(match.group(0)) - 1
                        if decimal_digits >= 3:
                            # If there are more than 3 decimal places, remove all periods
                            return float(str(value).replace('.', ''))
                return float(value)
            except ValueError:
                raise UserError(f"Invalid number format: {value}")

        df['Purchase Price'] = df['Purchase Price'].apply(normalize_value)
        df['Recommended Retail Price'] = df['Recommended Retail Price'].apply(normalize_value)
        df['Suggested Retail Price'] = df['Suggested Retail Price'].apply(normalize_value)
        df['Nett Purchase Price'] = df['Nett Purchase Price'].apply(normalize_value)

        # Fetch the 'Kave' tag from product_tag_ids
        kave_tag = self.env['product.tag'].search([('name', '=', 'Kave')], limit=1)
        if not kave_tag:
            kave_tag = self.env['product.tag'].create({'name': 'Kave'})
            _logger.info("'Kave' tag created.")
        else:
            _logger.info("'Kave' tag found.")

        # Fetch the 'Produtos Kave' category for both internal and eCommerce categories
        kave_category = self.env['product.category'].search([('name', '=', 'Produtos Kave')], limit=1)
        if not kave_category:
            all_category = self.env['product.category'].search([('name', '=', 'All')], limit=1)
            kave_category = self.env['product.category'].create({
                'name': 'Produtos Kave',
                'parent_id': all_category.id
            })
            _logger.info("'Produtos Kave' internal category created under 'All'.")

        kave_public_category = self.env['product.public.category'].search([('name', '=', 'Produtos Kave')], limit=1)
        if not kave_public_category:
            todas_category = self.env['product.public.category'].search([('name', '=', 'Todas')], limit=1)
            kave_public_category = self.env['product.public.category'].create({
                'name': 'Produtos Kave',
                'parent_id': todas_category.id
            })
            _logger.info("'Produtos Kave' public category created under 'Todas'.")

        pos_category = self.env['pos.category'].search([('name', '=', 'Produtos Kave')], limit=1)
        if not pos_category:
            pos_category = self.env['pos.category'].create({'name': 'Produtos Kave'})
            _logger.info("'Produtos Kave' POS category created.")

        # Fetch all existing products and their variants with the 'Kave' tag
        existing_kave_products = self.env['product.template'].search([('product_tag_ids', 'in', [kave_tag.id])])
        existing_kave_variant_codes = existing_kave_products.mapped('product_variant_ids.x_studio_referncia_interna')
        existing_kave_product_codes = existing_kave_products.mapped('x_studio_referncia_interna')

        # Combine both product template and variant codes
        all_existing_codes = set(existing_kave_product_codes) | set(existing_kave_variant_codes)

        _logger.info(f"Existing Kave product template codes (x_studio_referncia_interna): {existing_kave_product_codes}")
        _logger.info(f"Existing Kave product variant codes (x_studio_referncia_interna): {existing_kave_variant_codes}")
        _logger.info(f"Combined existing product and variant codes: {all_existing_codes}")

        # List of product codes from the Excel file
        imported_product_codes = df['Code'].tolist()
        _logger.info(f"Product codes in the Excel file: {imported_product_codes}")

        # Archive products that have the 'Kave' tag but are not in the Excel file
        products_to_archive = existing_kave_products.filtered(
            lambda p: (
                # Check using the custom fields if the product has variants
                (p.x_studio_referncia_interna and p.x_studio_referncia_interna not in imported_product_codes)
                if p.product_variant_count > 1 else
                # Check using default_code if there are no variants
                (p.default_code and p.default_code not in imported_product_codes)
            ) and not any(
                variant.x_studio_referncia_interna and variant.x_studio_referncia_interna in imported_product_codes 
                for variant in p.product_variant_ids)
        )

        # Fetch the default VAT tax (IVA 23%) from Odoo
        default_vat_tax = self.env['account.tax'].search([
            ('id', '=', 1567),  # Use the correct ID from the metadata screenshot
            ('type_tax_use', '=', 'sale')  # Ensure it's a sales tax
        ], limit=1)

        _logger.info(f"Products marked for archiving: {[p.x_studio_referncia_interna if p.product_variant_count > 1 else p.default_code for p in products_to_archive if p.x_studio_referncia_interna or p.default_code]}")

        for product in products_to_archive:
            _logger.info(f"Attempting to archive product: {product.name} ({product.x_studio_referncia_interna or product.default_code})")
            try:
                product.sudo().write({'active': False})
                self.env.cr.commit()  # Ensure the changes are saved
                _logger.info(f"Product archived successfully: {product.name} ({product.x_studio_referncia_interna or product.default_code})")
            except Exception as e:
                _logger.error(f"Failed to archive product: {product.name}. Error: {str(e)}")

        # Vendor for Kave Home
        kave_home_vendor = self.env['res.partner'].search([('name', '=', 'Kave Home')], limit=1)
        if not kave_home_vendor:
            raise UserError("Vendor 'Kave Home' not found. Please create this vendor.")

        ### ADDING ROUTE LOGIC FOR PRODUCTS ###
        # Routes: FRE/Stock -> Buy, BRA/Stock & SEI/Stock -> Supply
        buy_route = self.env['stock.route'].search([('name', '=', 'Comprar')], limit=1)
        if not buy_route:
            raise UserError('Buy Route not found')

        supply_route_1 = self.env['stock.route'].search([('name', '=', 'BRAGA: Supply Product from FREAMUNDE')], limit=1)
        supply_route_2 = self.env['stock.route'].search([('name', '=', 'SEIXAL: Supply Product from FREAMUNDE')], limit=1)
        if not supply_route_1 or not supply_route_2:
            raise UserError('Supply Route not found')

        valid_locations = {
            "FRE/Stock": {"parent": "FREAMUNDE", "route": buy_route},   # Buy Route
            "BRA/Stock": {"parent": "BRAGA", "route": supply_route_1},    # Supply Route Braga
            "SEI/Stock": {"parent": "SEIXAL", "route": supply_route_2}    # Supply Route Seixal
        }

        # Create or update the products from the Excel file
        for _, row in df.iterrows():
            _logger.info(f"Processing product: {row['Code']} - {row['Program']}")

            # Check for existing product template using either x_studio_referncia_interna or x_studio_cdigo_de_barras for variants
            code_value = row.get('Code')
            if not code_value:
                _logger.error(f"Missing 'Code' for row: {row}")
                continue  # Skip this row if 'Code' is missing
            
            # Search for an existing product template, including archived ones
            product_template = self.env['product.template'].search(
                [('x_studio_referncia_interna', '=', code_value), ('product_tag_ids', 'in', [kave_tag.id])],
                limit=1
            )

            if not product_template:
                product_template = self.env['product.template'].search(
                    [('x_studio_cdigo_de_barras', '=', row['EAN Code']), ('product_tag_ids', 'in', [kave_tag.id])],
                    limit=1
                )

            # If no active product is found, search for archived products
            if not product_template:
                archived_products = self.env['product.template'].search(
                    ['|',
                    ('x_studio_referncia_interna', '=', code_value),
                    ('x_studio_cdigo_de_barras', '=', row['EAN Code']),
                    ('product_tag_ids', 'in', [kave_tag.id]),
                    ('active', '=', False)
                    ],
                    order='create_date desc'  # Get the most recently archived product first
                )
                if archived_products:
                    # Unarchive the most recent archived product
                    product_template = archived_products[0]

                    # Ensure VAT tax is applied BEFORE activating the product
                    if not product_template.taxes_id or not product_template.taxes_id.filtered(lambda t: t.type_tax_use == 'sale'):
                        if default_vat_tax:
                            product_template.sudo().write({'taxes_id': [(6, 0, [default_vat_tax.id])]})
                            self.env.cr.commit()  # Force commit to database
                            _logger.info(f"Assigned VAT tax {default_vat_tax.name} to unarchived product {product_template.name}.")
                        else:
                            _logger.warning(f"Default VAT tax (ID 1567) not found! Cannot assign tax to {product_template.name}.")

                    # Now, AFTER assigning VAT tax, set active=True
                    product_template.sudo().write({'active': True})
                    self.env.cr.commit()  # Ensure activation is committed
                    _logger.info(f"Unarchived product: {product_template.name} ({product_template.x_studio_referncia_interna or product_template.default_code})")

            # Ensure purchase_price is defined
            purchase_price = row['Nett Purchase Price'] if pd.notna(row['Nett Purchase Price']) else 0.0

            # Process the weight package
            weight_package = str(row['Weight Package']) if pd.notna(row['Weight Package']) else '0'
            if '#' in weight_package:
                weights = [float(w.replace(',', '.')) for w in weight_package.split('#')]
                total_weight = sum(weights)
                volume_qty = len(weights)
                peso_cada_volume = ' / '.join(weight_package.split('#'))
            else:
                total_weight = float(weight_package.replace(',', '.'))
                volume_qty = 1
                peso_cada_volume = weight_package

            # Custom logic to populate the custom_attribute_ids table with "Colour" values
            #colours = str(row['Colour']).split(',') if pd.notna(row['Colour']) and row['Colour'] else []

            # Fetch or create the "Colour" attribute
            #attribute = self.env['product.attribute'].search([('name', '=', 'Colour')], limit=1)
            #if not attribute:
                #attribute = self.env['product.attribute'].create({'name': 'Colour'})

            # Ensure product_template exists
            #if product_template and product_template.id:
                #custom_attribute_obj = self.env['custom.product.attribute']  # Get the custom attribute model

                #for colour in colours:
                    # Check if an attribute for "Cor" already exists for this product and this specific colour
                    #existing_custom_attribute = custom_attribute_obj.search([
                        #('product_id', '=', product_template.id),
                        #('name', '=', 'Cor'),
                        #('description', '=', colour.strip())
                    #], limit=1)

                    #if not existing_custom_attribute:
                        #custom_attribute_vals = {
                            #'name': 'Cor',  # Attribute Name is always "Cor"
                            #'product_id': product_template.id,  # Link to the product template
                            #'description': colour.strip(),  # Populate with the respective value from the Colour column
                        #}
                        #custom_attribute_obj.create(custom_attribute_vals)
                        #_logger.info(f"Created custom attribute 'Cor' for {product_template.name} with colour value: {colour.strip()}")

            #else:
                #_logger.warning(f"Product template not found for {row['Code']}, skipping custom attribute creation.")

            # Update or create the product template
            if not product_template:
                _logger.info(f"Creating new product: {row['Program']}")
                product_vals = {
                    'name': row['Program'] if pd.notna(row['Program']) else '',
                    'x_studio_referncia_interna': row['Code'] if pd.notna(row['Code']) else '',
                    'description_sale': row['Description'] if pd.notna(row['Description']) else '',
                    'list_price': row['Suggested Retail Price'] if pd.notna(row['Suggested Retail Price']) else 0.0,
                    'standard_price': purchase_price,
                    'weight': total_weight,
                    'volume_qty': volume_qty,
                    'peso_cada_volume': peso_cada_volume,
                    'x_studio_stock_em_7_dias': row['Stock Blue'] if pd.notna(row['Stock Blue']) else 0.0,
                    'x_studio_stock_em_15_dias': row['Stock Red'] if pd.notna(row['Stock Red']) else 0.0,
                    'x_studio_stock_em_30_dias': row['Stock Grey'] if pd.notna(row['Stock Grey']) else 0.0,
                    'x_studio_preo_antes_desconto': row['Recommended Retail Price'] if pd.notna(row['Recommended Retail Price']) else 0.0,
                    'compare_list_price': row['Recommended Retail Price'] if pd.notna(row['Recommended Retail Price']) else 0.0,
                    'x_studio_desconto_aplicado_1': row['Discount'] if pd.notna(row['Discount']) else 0.0,
                    'default_code': row['Code'] if pd.notna(row['Code']) else '',
                    'barcode': row['EAN Code'] if pd.notna(row['EAN Code']) else '',
                    'sale_delay': 30,
                    'type': 'product',
                    'available_in_pos': True,
                    'allow_out_of_stock_order': True, 
                    'product_tag_ids': [(4, kave_tag.id)]
                }

                # Ensure VAT tax is set BEFORE website_published=True
                if default_vat_tax:
                    product_vals['taxes_id'] = [(6, 0, [default_vat_tax.id])]
                    _logger.info(f"Assigned VAT tax {default_vat_tax.name} to new product {row['Program']}")

                # Assign categories
                product_vals['categ_id'] = kave_category.id
                product_vals['public_categ_ids'] = [(6, 0, [kave_public_category.id])]
                product_vals['pos_categ_ids'] = [(6, 0, [pos_category.id])]

                # Check if compare_list_price is equal to list_price
                if row['Recommended Retail Price'] != row['Suggested Retail Price']:
                    product_vals['compare_list_price'] = row['Recommended Retail Price']
                else:
                    product_vals['compare_list_price'] = None

                # Set barcode
                product_vals['x_studio_cdigo_de_barras'] = row['EAN Code'] if pd.notna(row['EAN Code']) else ''

                # Create the product
                product_template = self.env['product.template'].create(product_vals)
                self.env.cr.commit()  # Ensure the creation is committed BEFORE publishing
                product_template.sudo().write({'website_published': True})
                _logger.info(f"Product created: {product_template.name}")
            else:
                _logger.info(f"Updating existing product: {product_template.name}")

                # Ensure existing products also have VAT tax
                if not product_template.taxes_id or not product_template.taxes_id.filtered(lambda t: t.type_tax_use == 'sale'):
                    if default_vat_tax:
                        product_template.sudo().write({'taxes_id': [(6, 0, [default_vat_tax.id])]})
                        self.env.cr.commit()  # Force commit to database
                        _logger.info(f"Added VAT tax {default_vat_tax.name} to existing product {product_template.name}.")
                    else:
                        _logger.warning(f"Default VAT tax (ID 1567) not found! Cannot assign tax to {product_template.name}.")

                product_vals = {
                    'name': row['Program'] if pd.notna(row['Program']) else '',
                    'description_sale': row['Description'] if pd.notna(row['Description']) else '',
                    'list_price': row['Suggested Retail Price'] if pd.notna(row['Suggested Retail Price']) else 0.0,
                    'standard_price': purchase_price,
                    'weight': total_weight,
                    'volume_qty': volume_qty,
                    'peso_cada_volume': peso_cada_volume,
                    'x_studio_stock_em_7_dias': row['Stock Blue'] if pd.notna(row['Stock Blue']) else 0.0,
                    'x_studio_stock_em_15_dias': row['Stock Red'] if pd.notna(row['Stock Red']) else 0.0,
                    'x_studio_stock_em_30_dias': row['Stock Grey'] if pd.notna(row['Stock Grey']) else 0.0,
                    'x_studio_preo_antes_desconto': row['Recommended Retail Price'] if pd.notna(row['Recommended Retail Price']) else 0.0,
                    'compare_list_price': row['Recommended Retail Price'] if pd.notna(row['Recommended Retail Price']) else 0.0,
                    'x_studio_desconto_aplicado_1': row['Discount'] if pd.notna(row['Discount']) else 0.0,
                    'default_code': row['Code'] if pd.notna(row['Code']) else '',
                    'barcode': row['EAN Code'] if pd.notna(row['EAN Code']) else '',
                    'sale_delay': 30,
                    'product_tag_ids': [(4, kave_tag.id)],
                    'allow_out_of_stock_order': True,
                    'available_in_pos': True
                }

                # Assign categories if missing
                if not product_template.categ_id:
                    product_vals['categ_id'] = kave_category.id
                if not product_template.public_categ_ids:
                    product_vals['public_categ_ids'] = [(6, 0, [kave_public_category.id])]
                if not product_template.pos_categ_ids:
                    product_vals['pos_categ_ids'] = [(6, 0, [pos_category.id])]

                product_template.write(product_vals)
                _logger.info(f"Product updated: {product_template.name}")

            ### Add logic for accessory products ###
            # Group products by 'Program' and link them as accessories to each other
            program = row.get('Program')

            if program:
                # Find all products that share the same Program value
                similar_products = self.env['product.template'].search([('name', '=', program)])

                if similar_products:
                    accessory_product_ids = []
                    for prod in similar_products:
                        # Fetch the product variant (product.product) linked to the product template (product.template)
                        if prod.product_variant_id and prod.product_variant_id.active and prod.product_variant_id.id != product_template.product_variant_id.id:
                            accessory_product_ids.append(prod.product_variant_id.id)

                    if accessory_product_ids:
                        # Append new accessories without removing existing ones
                        product_template.write({
                            'accessory_product_ids': [(4, prod_id) for prod_id in accessory_product_ids]
                        })
                        _logger.info(f"Added accessory products for {product_template.name} from program group: {program}")
                    else:
                        _logger.info(f"No valid accessory products found for {product_template.name}.")
                else:
                    _logger.warning(f"No accessory products found for program group: {program}")

            # Manage Supplier Information and apply Product Supplier Discount
            supplier_info = self.env['product.supplierinfo'].search([('product_tmpl_id', '=', product_template.id), ('partner_id', '=', kave_home_vendor.id)], limit=1)

            if supplier_info:
                supplier_info.write({
                    'price': row['Purchase Price'] if pd.notna(row['Purchase Price']) else 0.0,
                    'discount': row['Discount'] if pd.notna(row['Discount']) else 0.0,  # Product supplier discount from Excel
                    'currency_id': self.env.ref('base.EUR').id
                })
                _logger.info(f"Updated supplier info for {product_template.name}")
            else:
                self.env['product.supplierinfo'].create({
                    'partner_id': kave_home_vendor.id,
                    'product_tmpl_id': product_template.id,
                    'price': row['Purchase Price'] if pd.notna(row['Purchase Price']) else 0.0,
                    'discount': row['Discount'] if pd.notna(row['Discount']) else 0.0,  # Product supplier discount from Excel
                    'currency_id': self.env.ref('base.EUR').id
                })
                _logger.info(f"Created supplier info for {product_template.name}")

            # Update stock and synchronize with x_studio_quantidade_em_stock
            stock_quant = self.env['stock.quant'].search([
                ('product_id', '=', product_template.product_variant_id.id),
                ('location_id', '=', 54),  # Ensure stock is only applied to KAV/Stock
                ('company_id', '=', 2)  # Ensure stock is applied to the correct company
            ], limit=1)

            if stock_quant:
                stock_quant.sudo().write({
                    'quantity': row['Stock'] if pd.notna(row['Stock']) else 0.0,
                    'company_id': 2  # Explicitly set the company
                })
                product_template.write({'x_studio_quantidade_em_stock': str(stock_quant.quantity)})  # Synchronize stock
                _logger.info(f"Stock updated for {product_template.name} at KAV/Stock: {row['Stock']}")
            else:
                # Create new stock quant if none exists
                self.env['stock.quant'].sudo().create({
                    'product_id': product_template.product_variant_id.id,
                    'location_id': 54,  # Ensure stock is only applied to KAV/Stock
                    'company_id': 2,  # Explicitly set the company
                    'quantity': row['Stock'] if pd.notna(row['Stock']) else 0.0,
                })
                product_template.write({'x_studio_quantidade_em_stock': str(row['Stock'])})  # Set the custom field
                _logger.info(f"Stock created for {product_template.name} at KAV/Stock: {row['Stock']}")

            # Set the product's estimated date if available
            if pd.notna(row['Estimated Date (dd/mm/yyyy)']):
                try:
                    estimated_date = pd.to_datetime(row['Estimated Date (dd/mm/yyyy)'], format='%d/%m/%Y')
                    product_template.write({'x_studio_data_estimada_de_entrega': estimated_date})
                    _logger.info(f"Estimated delivery date set for {product_template.name}")
                except Exception as e:
                    _logger.error(f"Error setting estimated date for {product_template.name}: {str(e)}")

            ### SALE DELAY CHECKS ###
            # Ensure stock values are numbers before comparing
            def convert_to_number(value):
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return 0

            try:
                quantidade_em_stock = convert_to_number(product_template.x_studio_quantidade_em_stock) or 0.0
                stock_em_7_dias = convert_to_number(product_template.x_studio_stock_em_7_dias) or 0.0
                stock_em_15_dias = convert_to_number(product_template.x_studio_stock_em_15_dias) or 0.0
                stock_em_30_dias = convert_to_number(product_template.x_studio_stock_em_30_dias) or 0.0
                data_estimada = product_template.x_studio_data_estimada_de_entrega

                if data_estimada:
                    # Calculate the difference between the current date and the estimated delivery date
                    sale_delay_days = (data_estimada - fields.Date.context_today(self)).days
                    product_template.write({'sale_delay': sale_delay_days})
                    _logger.info(f"Sale delay set to {sale_delay_days} days for {product_template.name} based on estimated delivery date.")
                else:
                    # Handle conditions based on stock levels
                    if quantidade_em_stock > 0:
                        product_template.write({'sale_delay': 30})
                    elif quantidade_em_stock == 0 and stock_em_7_dias > 0:
                        product_template.write({'sale_delay': 45})
                    elif quantidade_em_stock == 0 and stock_em_7_dias == 0 and stock_em_15_dias > 0:
                        product_template.write({'sale_delay': 60})
                    elif quantidade_em_stock == 0 and stock_em_7_dias == 0 and stock_em_15_dias == 0 and stock_em_30_dias > 0:
                        product_template.write({'sale_delay': 70})
                    else:
                        product_template.write({'sale_delay': 30})  # Default if no conditions are met

                    _logger.info(f"Sale delay set to {product_template.sale_delay} days for {product_template.name} based on stock conditions.")
            except Exception as e:
                _logger.error(f"Error setting sale delay for product {product_template.name}: {str(e)}")

            for loc_name, data in valid_locations.items():
                specific_location = self.env['stock.location'].search([
                    ('name', '=', 'Stock'),
                    ('location_id.name', '=', data["parent"])
                ], limit=1)

                if not specific_location:
                    _logger.warning(f"Specified location not found for {loc_name} ({data['parent']}). Skipping route assignment.")
                    continue  # Skip if the location is not found

                reordering_rule = self.env['stock.warehouse.orderpoint'].search([
                    ('product_id', '=', product_template.product_variant_id.id),
                    ('location_id', '=', specific_location.id),
                    ('company_id', '=', 2),  # Apply to Company ID = 2
                ], limit=1)

                if not reordering_rule:
                    self.env['stock.warehouse.orderpoint'].create({
                        'product_id': product_template.product_variant_id.id,
                        'location_id': specific_location.id,
                        'company_id': 2,  # Ensure it's under Company 2
                        'route_id': data["route"].id,
                        'product_min_qty': 0.0,  # Prevent NULL errors
                        'product_max_qty': 0.0,
                        'qty_multiple': 1.0,
                        'trigger': 'auto',
                    })
                    _logger.info(f'Created reordering rule for {product_template.name} at {loc_name} ({data["parent"]})')
                else:
                    _logger.info(f'Reordering rule already exists for {product_template.name} at {loc_name} ({data["parent"]})')

        _logger.info("Kave product import process completed.")
        #  Call the email function BEFORE returning
        self.send_success_email()
        return {'type': 'ir.actions.act_window_close'}
