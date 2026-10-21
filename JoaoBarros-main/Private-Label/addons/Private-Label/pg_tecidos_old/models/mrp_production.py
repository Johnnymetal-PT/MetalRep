import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    product_description_variants = fields.Char()
    partner_id = fields.Many2one(
        'res.partner',
        string='Fornecedor',
        domain="['|', ('company_id', '=', company_id), ('company_id', 'parent_of', company_id)]",
    )

    @api.model
    def create(self, vals):
        # Check if product_description_variants is empty
        description = str(vals.get('product_description_variants') or '').strip()
        if not description:
            sale_order_line = self.env['sale.order.line'].search([('product_id', '=', vals.get('product_id'))], limit=1)
            if sale_order_line:
                description = sale_order_line.name
                vals['product_description_variants'] = description
                _logger.info(f"[CREATE] Set product_description_variants to product name: {description}")
            else:
                _logger.warning(f"[CREATE] No sale.order.line found for product_id: {vals.get('product_id')}")

        terms = {
            'ACABAMENTO': '',
            'ACABAMENTO com Ponteira': '',
            'TECIDO COSTAS FRENTE + ASSENTO': '',
            'TECIDO COSTAS TRÁS': '',
            'TECIDO CIMA': '',
            'TECIDO BAIXO': '',
            'TECIDO': '',
            'ARO': '',
            'ALTERAÇÃO COR DOS PÉS': ''
        }

        _logger.info(f"[CREATE] Product description variants: {description}")

        # Extract the text for each term
        for term in terms:
            start_index = description.lower().find(f"{term.lower()}:")
            if start_index != -1:
                end_index = len(description)
                for next_term in terms:
                    if next_term != term:
                        next_start = description.lower().find(f"{next_term.lower()}:", start_index + len(term) + 1)
                        if next_start != -1:
                            end_index = min(end_index, next_start)
                terms[term] = description[start_index + len(term) + 1:end_index].strip()
                _logger.info(f"[CREATE] Extracted term '{term}': {terms[term]}")

        # Fetch "DIMENSÕES DO COLCHÃO" from product variant attribute values
        sale_order_line = self.env['sale.order.line'].search([('product_id', '=', vals.get('product_id'))], limit=1)
        if sale_order_line:
            dimensoes_value = sale_order_line.product_template_attribute_value_ids.filtered(
                lambda ptav: ptav.attribute_id.name == 'DIMENSÕES DO COLCHÃO'
            ).name
            if dimensoes_value:
                terms['DIMENSÕES DO COLCHÃO'] = dimensoes_value
                _logger.info(f"[CREATE] Selected DIMENSÕES DO COLCHÃO: {dimensoes_value}")

        # Update the product_description_variants with all terms (ensuring no duplication)
        existing_description = vals.get('product_description_variants', '').strip()

        # Parse existing terms into a dictionary
        existing_terms = {}
        if existing_description:
            for item in existing_description.split(', '):
                if ': ' in item:
                    key, value = item.split(': ', 1)
                    existing_terms[key] = value

        # Merge existing terms with new terms
        for term, value in terms.items():
            if value:  # Only update terms with a non-empty value
                existing_terms[term] = value

        # Rebuild the product_description_variants field
        vals['product_description_variants'] = ', '.join(f"{key}: {value}" for key, value in existing_terms.items())
        _logger.info(f"[CREATE] Final product_description_variants: {vals['product_description_variants']}")

        product_qty = sale_order_line.product_uom_qty if sale_order_line else 1

        # Step 1: Search the oldest BoM for the product and map terms to texts
        oldest_bom, term_to_text = self._search_oldest_bom(vals.get('product_id'), terms)

        # Step 2: Duplicate the BoM (prevent modifying the oldest BoM)
        duplicated_bom = self._duplicate_bom(oldest_bom, product_qty)

        # Only apply consumption values if duplicated_bom is not None
        if duplicated_bom:
            # Step 3: Update the duplicated BoM lines with consumption values before assigning duplicated products
            self._apply_consumption_values(duplicated_bom, term_to_text, product_qty)

            # Step 4: Duplicate products based on terms and update the duplicated BoM
            for term, extracted_text in term_to_text.items():
                if extracted_text:
                    self._duplicate_and_assign_to_bom(duplicated_bom, term, extracted_text)

        # Step 5: Create the Manufacturing Order
        vals['state'] = 'draft'
        production = super(MrpProduction, self).create(vals)
        if duplicated_bom:
            production.write({'bom_id': duplicated_bom.id})
            _logger.info(f"[CREATE] Assigned duplicated BoM {duplicated_bom.id} to Manufacturing Order {production.id}")

        return production

    def _search_oldest_bom(self, product_id, terms):
        product = self.env['product.product'].browse(product_id)
        bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', product.product_tmpl_id.id)], order='create_date asc', limit=1)
        _logger.info(f"[BOM] Found oldest BoM for product {product.product_tmpl_id.id}: {bom.id if bom else 'No BoM found'}")

        term_to_text = {}
        if bom:
            for line in bom.bom_line_ids:
                product_name = line.product_id.name.lower()
                if 'tecido costas trás' in product_name:
                    term = 'TECIDO COSTAS TRÁS'
                elif 'tecido costas frente + assento' in product_name:
                    term = 'TECIDO COSTAS FRENTE + ASSENTO'
                elif 'tecido cima' in product_name:
                    term = 'TECIDO CIMA'
                elif 'tecido baixo' in product_name:
                    term = 'TECIDO BAIXO'
                elif 'tecido' in product_name:
                    term = 'TECIDO'
                elif 'aro' in product_name:
                    term = 'ARO'
                elif 'alteração cor dos pés' in product_name:
                    term = 'ALTERAÇÃO COR DOS PÉS'
                elif 'acabamento com ponteira' in product_name:
                    term = 'ACABAMENTO com Ponteira'
                elif 'acabamento' in product_name and 'com ponteira' not in product_name:
                    term = 'ACABAMENTO'
                else:
                    _logger.info(f"[BOM] Skipping BoM line product {line.product_id.id}, as it doesn't match specified terms.")
                    continue

                extracted_text = terms.get(term.replace(' com Ponteira', ''))
                term_to_text[term] = extracted_text
                _logger.info(f"[BOM] Extracted text for term '{term}': {extracted_text}")

        return bom, term_to_text

    def _duplicate_bom(self, bom, product_qty):
        if bom:
            duplicated_bom = bom.copy()
            _logger.info(f"[BOM] Duplicated BoM {bom.id} to new BoM {duplicated_bom.id}")

            if duplicated_bom.product_qty != product_qty:
                duplicated_bom.product_qty = product_qty
                _logger.info(f"[BOM] Updated duplicated BoM product_qty to {product_qty}")

            # Update product quantities in the duplicated BoM lines
            for line in duplicated_bom.bom_line_ids:
                product_name = line.product_id.name.lower()

                # Skip if this line is going to be updated by _apply_consumption_values
                is_term_component = any(term.lower() in product_name for term in [
                    'tecido costas trás',
                    'tecido costas frente + assento',
                    'tecido cima',
                    'tecido baixo',
                    'tecido',
                    #'aro',
                    #'alteração cor dos pés',
                    #'acabamento com ponteira',
                    #'acabamento'
                ])

                if not is_term_component:
                    original_qty = line.product_qty
                    scaled_qty = original_qty * product_qty
                    line.product_qty = scaled_qty
                    _logger.info(f"[BOM] Scaled non-term component {line.product_id.name}: Original Qty {original_qty}, New Qty {scaled_qty}")
                else:
                    _logger.info(f"[BOM] Skipping term component {line.product_id.name} in bulk scaling step.")

            return duplicated_bom
        return None

    def _apply_consumption_values(self, bom, term_to_text, product_qty):
        """
        Apply the appropriate consumption values to BoM lines in the duplicated BoM
        based on the original component/material in the original BoM.
        """
        if not bom:
            return

        for line in bom.bom_line_ids:
            product_name = line.product_id.name.lower()

            # Determine the matching term for the BoM line
            if 'tecido costas trás' in product_name:
                term = 'TECIDO COSTAS TRÁS'
            elif 'tecido costas frente + assento' in product_name or 'tecido completo' in product_name:
                term = 'TECIDO COSTAS FRENTE + ASSENTO'
            elif 'tecido cima' in product_name:
                term = 'TECIDO CIMA'
            elif 'tecido baixo' in product_name:
                term = 'TECIDO BAIXO'
            elif 'tecido' in product_name:
                term = 'TECIDO'
            else:
                _logger.info(f"[BOM] Skipping BoM line product {line.product_id.id}, as it doesn't match specified terms.")
                continue

            # Apply the consumption value if the term matches
            if term in term_to_text:
                component_template = line.product_id.product_tmpl_id  # Component in the BoM line

                # Fetch the per-unit consumption value from the component's own table
                consumption_value_per_unit = self._get_consumption_value(component_template, product_qty)

                # Calculate the total consumption value based on the product quantity
                total_consumption_value = consumption_value_per_unit * product_qty

                # Update product_qty only if different from the current value
                if line.product_qty != total_consumption_value:
                    line.product_qty = total_consumption_value
                    _logger.info(
                        f"[BOM] Updated BoM line {line.id}: "
                        f"Component: {component_template.name}, "
                        f"Per-unit value: {consumption_value_per_unit}, "
                        f"Product Qty: {product_qty}, "
                        f"Total Consumption Value: {total_consumption_value}"
                    )
                else:
                    _logger.info(f"[BOM] Skipping BoM line {line.id}, consumption value already correct.")

    def _duplicate_and_assign_to_bom(self, bom, term, extracted_text):
        if bom:
            main_product_name = bom.product_tmpl_id.name  # Get the main product's name from the BoM
            product_in_bom = bom.bom_line_ids.filtered(
                lambda line: term.lower() in line.product_id.name.lower() or 
                            ('tecido completo' in line.product_id.name.lower() and term.lower() in ['tecido costas frente + assento', 'tecido cima'])
            )

            if product_in_bom:
                for line in product_in_bom:
                    product = line.product_id.product_tmpl_id
                    _logger.info(f"[DUPLICATE] Found product for '{term}' in BoM: {product.id} - {product.name}")

                    # Define duplicate name based on term specifics
                    duplicate_name = extracted_text
                    if 'acabamento com ponteira' in product.name.lower():
                        duplicate_name = f"{main_product_name} {extracted_text} com Ponteira"
                        _logger.info(f"[DUPLICATE] Appending 'com Ponteira' to the name for product '{product.name}'")

                    elif 'acabamento' in product.name.lower() or 'aro' in product.name.lower() or 'alteração cor dos pés' in product.name.lower():
                        duplicate_name = f"{main_product_name} {extracted_text}"
                        _logger.info(f"[DUPLICATE] Prepending main product name '{main_product_name}' to '{extracted_text}'")

                    elif 'tecido costas frente + assento' in term.lower() or 'tecido costas trás' in term.lower() or 'tecido cima' in term.lower() or 'tecido baixo' in term.lower() or term.lower() == 'tecido':
                        duplicate_name = f"Tecido {extracted_text}"
                        _logger.info(f"[DUPLICATE] Prefixed 'Tecido' to '{extracted_text}' for term '{term}'")

                    # Check if a product with this name already exists
                    existing_product = self.env['product.template'].search([('name', '=', duplicate_name)], order="create_date desc")
                    if existing_product:
                        if len(existing_product) > 1:
                            existing_product[1:].write({'active': False})
                        duplicate_product = existing_product[0]
                        _logger.info(f"[DUPLICATE] Product '{duplicate_name}' already exists, using existing product ID: {duplicate_product.id}")
                    else:
                        duplicate_product = product.copy()
                        duplicate_product.name = duplicate_name
                        self._copy_custom_fields(product, duplicate_product)
                        _logger.info(f"[DUPLICATE] Created new product: {duplicate_product.name}")

                        self._assign_vendor_to_product(duplicate_product, term)

                    line.write({'product_id': duplicate_product.product_variant_id.id})
                    _logger.info(f"[BOM] Replaced original product {line.product_id.id} with duplicated product {duplicate_product.product_variant_id.id} in BoM line")
            else:
                _logger.info(f"[CREATE] No matching product found in BoM for term '{term}', skipping.")

    def _assign_vendor_to_product(self, duplicate_product, term):
        vendor_name = None
        if term in ['TECIDO COSTAS FRENTE + ASSENTO', 'TECIDO COSTAS TRÁS', 'TECIDO CIMA', 'TECIDO BAIXO', 'TECIDO']:
            vendor_name = '-Fornecedor de tecidos a definir'
        elif 'ACABAMENTO' in term or term == 'ARO' or term == 'ALTERAÇÃO COR DOS PÉS':
            vendor_name = 'Polidor C/Arte Mobiliario, Lda'

        if vendor_name:
            vendor = self.env['res.partner'].search([('name', '=', vendor_name)], limit=1)
            if vendor:
                self.env['product.supplierinfo'].create({
                    'product_tmpl_id': duplicate_product.id,
                    'partner_id': vendor.id,
                    'min_qty': 0.00,
                    'price': 0.00,
                    'currency_id': self.env.user.company_id.currency_id.id,
                    'delay': 7,
                    'date_start': fields.Date.today(),
                })
                _logger.info(f"[VENDOR] Assigned vendor '{vendor_name}' to product {duplicate_product.name}")
            else:
                _logger.warning(f"[VENDOR] Vendor '{vendor_name}' not found for product {duplicate_product.name}")

    def _get_consumption_value(self, product_template, product_qty):
        """
        Fetch the per-unit consumption value from the component's consumption table
        based on the quantity. It dynamically selects the correct row.
        """
        _logger.info(f"Fetching consumption values for component: {product_template.name}, Quantity: {product_qty}")

        # Extract the consumption values from the component's backoffice Consumption Table
        consumption_table = [
            product_template.price_1, product_template.price_2, product_template.price_3,
            product_template.price_4, product_template.price_5, product_template.price_6,
            product_template.price_7, product_template.price_8, product_template.price_9,
            product_template.price_10
        ]

        _logger.info(f"Consumption table values for {product_template.name}: {consumption_table}")

        # Ensure product_qty is valid and calculate the index
        if product_qty < 1:
            _logger.warning(f"Invalid quantity ({product_qty}). Defaulting to the first value in the table.")
            return consumption_table[0]  # Default to the first value if the quantity is less than 1

        index = min(int(product_qty) - 1, len(consumption_table) - 1)  # Adjust for 0-based indexing
        selected_value = consumption_table[index]

        _logger.info(
            f"Selected consumption value for Component: {product_template.name}, "
            f"Quantity: {product_qty}, "
            f"Selected Row: {index + 1}, "
            f"Value: {selected_value}"
        )
        return selected_value
            
    def _copy_custom_fields(self, original_product, duplicate_product):
        """
        Copy custom fields (like the consumption table) from the original product to the duplicate product.
        """
        try:
            # List of custom fields to copy
            custom_fields = [
                'price_1', 'price_2', 'price_3', 'price_4', 'price_5',
                'price_6', 'price_7', 'price_8', 'price_9', 'price_10'
            ]

            for field in custom_fields:
                setattr(duplicate_product, field, getattr(original_product, field, 0.0))
            
            _logger.info(f"[COPY] Successfully copied custom fields from product {original_product.id} to {duplicate_product.id}")
        except Exception as e:
            _logger.error(f"[COPY] Failed to copy custom fields from product {original_product.id} to {duplicate_product.id}: {str(e)}")
