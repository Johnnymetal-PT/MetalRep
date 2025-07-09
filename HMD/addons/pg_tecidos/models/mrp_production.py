import logging
import re
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    product_description_variants = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        productions = self.browse()
        used_lines = set()

        for vals in vals_list:
            # 1. Try to fetch related sale.order.line
            sale_order_line = self.env['sale.order.line'].search([('product_id', '=', vals.get('product_id'))], limit=1)
            product_qty = sale_order_line.product_uom_qty if sale_order_line else 1

            # 2. Get product description
            description = str(vals.get('product_description_variants') or '').strip()
            if not description and sale_order_line:
                description = sale_order_line.name
                _logger.info(f"[CREATE] Fallback to sale.order.line.name: {description}")

            # 3. Extract raw terms from the description
            matches = re.findall(
                r'([A-ZÀ-Ú\s\+\-]+):\s*([^\n]+?)(?=\n[A-ZÀ-Ú\s\+\-]+:|$)',
                description,
                re.IGNORECASE
            )
            parsed_terms = {}

            for line in description.splitlines():
                if ':' in line:
                    key_part, value_part = line.split(':', 1)
                    key_clean = key_part.strip().upper()
                    value_clean = value_part.strip().rstrip(':')
                    parsed_terms[key_clean] = value_clean
                    _logger.info(f"[PARSE] Term extracted: '{key_clean}' → '{value_clean}'")

            # 4. Fill expected terms with fallback values
            expected_terms = [
                'ACABAMENTO', 'ACABAMENTO com Ponteira', 'TECIDO COSTAS FRENTE + ASSENTO',
                'TECIDO COSTAS TRÁS', 'TECIDO CIMA', 'TECIDO BAIXO', 'TECIDO', 'ARO',
                'SIZE', 'FINISH', 'ALTERAÇÃO COR DOS PÉS'
            ]
            normalized_terms = {term: '' for term in expected_terms}
            for term in expected_terms:
                for key in parsed_terms:
                    if term.upper() in key:
                        normalized_terms[term] = parsed_terms[key]

            # 5. Build the joined description for recordkeeping
            description_joined = "\n".join(
                f"{key}: {value}" for key, value in normalized_terms.items() if value
            )
            vals['product_description_variants'] = description_joined
            _logger.info(f"[CREATE] Final product_description_variants:\n{description_joined}")

            # 6. Generate and adjust BoM
            oldest_bom, term_to_text = self._search_oldest_bom(vals.get('product_id'), normalized_terms)
            duplicated_bom = self._duplicate_bom(oldest_bom, product_qty)

            if duplicated_bom:
                self._apply_consumption_values(duplicated_bom, term_to_text, product_qty)
                self._duplicate_and_assign_to_bom(duplicated_bom, parsed_terms, used_lines)

            # 7. Create the MO
            vals['state'] = 'draft'
            production = super().create([vals])
            if duplicated_bom:
                production.write({'bom_id': duplicated_bom.id})
                _logger.info(f"[CREATE] Assigned duplicated BoM {duplicated_bom.id} to Manufacturing Order {production.id}")

            productions += production

        return productions

    def _search_oldest_bom(self, product_id, terms):
        product = self.env['product.product'].browse(product_id)

        # Get the oldest BoM for the product template
        bom = self.env['mrp.bom'].search(
            [('product_tmpl_id', '=', product.product_tmpl_id.id)],
            order='create_date asc',
            limit=1
        )

        _logger.info(f"[BOM] Found oldest BoM for product {product.product_tmpl_id.id}: {bom.id if bom else 'No BoM found'}")

        term_to_text = {}

        if bom:
            for line in bom.bom_line_ids:
                product_name = line.product_id.name.lower()

                # Identify which term is associated with the component
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
                elif 'size' in product_name:
                    term = 'SIZE'
                elif 'finish' in product_name:
                    term = 'FINISH'
                elif 'acabamento' in product_name and 'com ponteira' not in product_name:
                    term = 'ACABAMENTO'
                else:
                    _logger.info(f"[BOM] Skipping BoM line product {line.product_id.id}, as it doesn't match specified terms.")
                    continue

                # ✅ Use the exact term key as-is (no normalization) to extract its mapped value
                extracted_text = terms.get(term, '').strip()

                # Save the extracted value into the dictionary
                term_to_text[term] = extracted_text

                if extracted_text:
                    _logger.info(f"[BOM] Extracted text for term '{term}': {extracted_text}")
                else:
                    _logger.warning(f"[BOM] No extracted text found for term '{term}' in parsed terms.")

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

    def _duplicate_and_assign_to_bom(self, bom, parsed_terms, used_lines):
        if not bom:
            return

        for line in bom.bom_line_ids:
            if line.id in used_lines:
                continue

            original_product = line.product_id
            original_template = original_product.product_tmpl_id
            original_name = original_template.name
            original_name_lower = original_name.lower()

            _logger.info(f"[CHECK] Processing BoM line '{original_name}'")

            replacements = {}

            for term, value in parsed_terms.items():
                term_clean = term.strip().lower()
                value_clean = value.strip().rstrip(':')

                match = re.search(rf'\b{re.escape(term_clean)}\b', original_name_lower)
                if match:
                    replacements[term_clean] = value_clean
                    _logger.info(f"[MATCH] Term '{term_clean}' matched in '{original_name_lower}' → Replace with: '{value_clean}'")
                else:
                    _logger.debug(f"[NO MATCH] Term '{term_clean}' not found in '{original_name_lower}'")

            if not replacements:
                _logger.info(f"[REPLACEMENTS] No matching terms found in '{original_name}'. Skipping.")
                continue

            new_name = original_name
            for placeholder, replacement in replacements.items():
                pattern = re.compile(rf'\b{re.escape(placeholder)}\b', re.IGNORECASE)
                new_name = pattern.sub(replacement, new_name)

            new_name = re.sub(r'\s+', ' ', new_name).replace(':', '').strip()

            if new_name == original_name:
                _logger.info(f"[REPLACEMENTS] Name unchanged for '{original_name}'. Skipping update.")
                continue

            used_lines.add(line.id)
            _logger.info(f"[REPLACEMENTS] Final name change: '{original_name}' → '{new_name}' with replacements: {replacements}")

            existing_product = self.env['product.template'].search([
                ('name', '=', new_name)
            ], order="create_date desc")

            if existing_product:
                if len(existing_product) > 1:
                    existing_product[1:].write({'active': False})
                duplicate_product = existing_product[0]
                _logger.info(f"[DUPLICATE] Reusing product '{new_name}', ID: {duplicate_product.id}")
            else:
                duplicate_product = original_template.copy()
                duplicate_product.name = new_name
                self._copy_custom_fields(original_template, duplicate_product)

                first_term = list(replacements.keys())[0].upper()
                self._assign_vendor_to_product(duplicate_product, first_term)
                _logger.info(f"[DUPLICATE] Created new product: {duplicate_product.name}")

            line.write({'product_id': duplicate_product.product_variant_id.id})
            _logger.info(f"[BOM] Updated BoM line {line.id} with product '{duplicate_product.name}'")

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