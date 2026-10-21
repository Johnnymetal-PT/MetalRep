import logging
import re
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    #description_sale = fields.Char()
    partner_id = fields.Many2one(
        'res.partner',
        string='Fornecedor',
        domain="['|', ('company_id', '=', company_id), ('company_id', 'parent_of', company_id)]",
    )

    description_sale = fields.Text(string="Sale Line Description")

    # Inside mrp.production
    @api.model
    def create(self, vals):
        res = super().create(vals)
        if vals.get('origin'):
            sale_order = self.env['sale.order'].search([('name', '=', vals['origin'])], limit=1)
            if sale_order:
                # Look for the sale order line matching the product
                sol = sale_order.order_line.filtered(lambda l: l.product_id.id == vals.get('product_id'))
                if sol:
                    res.description_sale = sol[0].name  # or .customer_lead or another description field
        return res

    @api.model
    def create(self, vals):
        # Safely populate description_sale from the correct sale.order.line
        description = vals.get('description_sale', '').strip()
        if not description and vals.get('origin') and vals.get('product_id'):
            sale_order_line = self.env['sale.order.line'].search([
                ('order_id.name', '=', vals.get('origin')),
                ('product_id', '=', vals.get('product_id'))
            ], limit=1)
            if sale_order_line:
                description = sale_order_line.name
                vals['description_sale'] = description
                _logger.info(f"[CREATE] Matched SO line for product {sale_order_line.product_id.name}: description_sale set to '{description}'")
            else:
                _logger.warning(f"[CREATE] No matching sale.order.line found for SO '{vals.get('origin')}' and product_id: {vals.get('product_id')}")

        terms = {
            'Vivos': '',
            'Acabamento': '',
            'Costa Interior e Assento': '',
            'Costa Exterior': '',
            'Tecido': '',
            'Tecido1': '',
            'Tecido2': '',
            'Tecido3': '',
            'Pele': '',
            'Pele1': '',
            'Pele2': '',
            'Pele3': '',
            'Estrutura': '',
            'Metal': ''
        }

        _logger.info(f"[CREATE] Product description variants: {description}")

        # Extract standard terms from description_sale
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

        # Extract TX terms from product display_name
        product = self.env['product.product'].browse(vals.get('product_id'))
        tx_extracted = self._extract_tx_terms_from_product_name(product.display_name)
        for k, v in tx_extracted.items():
            if v:
                _logger.info(f"[TX MERGE] Overwriting term '{k}' with TX value: {v}")
                terms[k] = v
            else:
                _logger.info(f"[TX MERGE] Skipping overwrite of term '{k}' because TX value is empty.")
        _logger.info(f"[TX EXTRACT] From product name '{product.display_name}', extracted TX terms: {tx_extracted}")

        """ Add DIMENSÕES DO COLCHÃO
        sale_order_line = self.env['sale.order.line'].search([('product_id', '=', vals.get('product_id'))], limit=1)
        if sale_order_line:
            dimensoes_value = sale_order_line.product_template_attribute_value_ids.filtered(
                lambda ptav: ptav.attribute_id.name == 'DIMENSÕES DO COLCHÃO'
            ).name
            if dimensoes_value:
                terms['DIMENSÕES DO COLCHÃO'] = dimensoes_value
                _logger.info(f"[CREATE] Selected DIMENSÕES DO COLCHÃO: {dimensoes_value}")"""

        # Start with clean description from SO line
        description_lines = []

        # Add initial product label (from SO line name)
        if description:
            first_line = description.splitlines()[0]
            description_lines.append(first_line)

        # Add structured terms (without repeating)
        for term in ['Costa Exterior', 'Costa Interior e Assento', 'Vivos', 'Acabamento', 'Metal', 'Tecido', 'Tecido1', 'Tecido2', 'Tecido3', 'Estrutura', 'Pele', 'Pele1', 'Pele2', 'Pele3']:
            value = terms.get(term)
            if value:
                description_lines.append(f"{term}: {value}")

        vals['description_sale'] = '\n'.join(description_lines)
        _logger.info(f"[CREATE] Final cleaned description_sale:\n{vals['description_sale']}")

        product_qty = sale_order_line.product_uom_qty if sale_order_line else 1

        oldest_bom, term_to_text = self._search_oldest_bom(vals.get('product_id'), terms)
        duplicated_bom = self._duplicate_bom(oldest_bom, product_qty)

        if duplicated_bom:
            self._apply_consumption_values(duplicated_bom, term_to_text, product_qty)
            for term, extracted_text in term_to_text.items():
                if extracted_text:
                    self._duplicate_and_assign_to_bom(duplicated_bom, term, extracted_text)

        vals['state'] = 'draft'
        production = super(MrpProduction, self).create(vals)
        if duplicated_bom:
            production.write({'bom_id': duplicated_bom.id})
            _logger.info(f"[CREATE] Assigned duplicated BoM {duplicated_bom.id} to Manufacturing Order {production.id}")

        return production

    def _extract_tx_terms_from_product_name(self, product_name):
        tx_terms = {
            'Costa Interior e Assento': '',
            'Costa Exterior': '',
            'Tecido': '',
            'Tecido1': '',
            'Tecido2': '',
            'Tecido3': '',
            'Pele': '',
            'Pele1': '',
            'Pele2': '',
            'Pele3': '',
            'Vivos': '',
        }

        match = re.search(r'\((.*?)\)', product_name)
        if not match:
            return tx_terms

        segments = [seg.strip() for seg in match.group(1).split(',')]
        tx_keywords = [
            'COM', 'Fabric Categ. A', 'Fabric Categ. B',
            'Fabric Categ. C', 'Fabric Categ. D',
            'Fabric Categ. E', 'Fabric Categ. F'
        ]

        matches = []
        i = 0
        while i < len(segments):
            if any(segments[i].startswith(key) for key in tx_keywords):
                next_val = segments[i + 1] if i + 1 < len(segments) else ''
                matches.append(f"{segments[i]} {next_val}".strip())
                i += 1  # skip next
            i += 1

        if len(matches) == 1:
            tx_terms['Tecido'] = matches[0]
        elif len(matches) >= 2:
            tx_terms['Costa Interior e Assento'] = matches[0]
            tx_terms['Costa Exterior'] = matches[1]

        return tx_terms
        
    def _search_oldest_bom(self, product_id, terms):
        product = self.env['product.product'].browse(product_id)
        bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', product.product_tmpl_id.id)], order='create_date asc', limit=1)
        _logger.info(f"[BOM] Found oldest BoM for product {product.product_tmpl_id.id}: {bom.id if bom else 'No BoM found'}")

        term_to_text = {}
        if bom:
            for line in bom.bom_line_ids:
                product_name = line.product_id.name.lower()
                if 'costa exterior' in product_name:
                    term = 'Costa Exterior'
                elif 'costa interior e assento' in product_name:
                    term = 'Costa Interior e Assento'
                elif 'acabamento' in product_name:
                    term = 'Acabamento'
                elif 'metal' in product_name:
                    term = 'Metal'
                elif 'tecido' in product_name:
                    term = 'Tecido'
                elif 'tecido1' in product_name:
                    term = 'Tecido1'
                elif 'tecido2' in product_name:
                    term = 'Tecido2'
                elif 'tecido3' in product_name:
                    term = 'Tecido3'
                elif 'pele' in product_name:
                    term = 'Pele'
                elif 'pele1' in product_name:
                    term = 'Pele1'
                elif 'pele2' in product_name:
                    term = 'Pele2'
                elif 'pele3' in product_name:
                    term = 'Pele3'
                elif 'vivos' in product_name:
                    term = 'Vivos'
                elif 'estrutura' in product_name:
                    term = 'Estrutura'
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
                    'costa exterior',
                    'costa interior e assento',
                    'tecido',
                    'tecido1',
                    'tecido2',
                    'tecido3',
                    'pele',
                    'pele1',
                    'pele2',
                    'pele3',
                    'vivos',
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
            if 'costa exterior' in product_name:
                term = 'Costa Exterior'
            elif 'costa interior e assento' in product_name:
                term = 'Costa Interior e Assento'
            elif 'tecido' in product_name:
                term = 'Tecido'
            elif 'tecido1' in product_name:
                term = 'Tecido1'
            elif 'tecido2' in product_name:
                term = 'Tecido2'
            elif 'tecido3' in product_name:
                term = 'Tecido3'
            elif 'pele' in product_name:
                term = 'Pele'
            elif 'pele1' in product_name:
                term = 'Pele1'
            elif 'pele2' in product_name:
                term = 'Pele2'
            elif 'pele3' in product_name:
                term = 'Pele3'
            elif 'vivos' in product_name:
                term = 'Vivos'
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
                            ('tecido completo' in line.product_id.name.lower() and term.lower() in ['costa interior e assento', 'costa exterior'])
            )

            if product_in_bom:
                for line in product_in_bom:
                    product = line.product_id.product_tmpl_id
                    _logger.info(f"[DUPLICATE] Found product for '{term}' in BoM: {product.id} - {product.name}")

                    # Define duplicate name based on term specifics
                    duplicate_name = extracted_text
                    """if 'acabamento com ponteira' in product.name.lower():
                        duplicate_name = f"{main_product_name} {extracted_text} com Ponteira"
                        _logger.info(f"[DUPLICATE] Appending 'com Ponteira' to the name for product '{product.name}'")"""
                    if 'acabamento' in product.name.lower() or 'metal' in product.name.lower() or 'estrutura' in product.name.lower():
                        duplicate_name = f"{main_product_name} {extracted_text}"
                        _logger.info(f"[DUPLICATE] Prepending main product name '{main_product_name}' to '{extracted_text}'")

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

                        #self._assign_vendor_to_product(duplicate_product, term)

                    line.write({
                        'product_id': duplicate_product.product_variant_id.id,
                        'product_uom_id': duplicate_product.uom_id.id
                    })
                    _logger.info(f"[BOM] Replaced product {line.product_id.id} and updated UoM to match product UoM {duplicate_product.uom_id.name}")
            else:
                _logger.info(f"[CREATE] No matching product found in BoM for term '{term}', skipping.")

    """def _assign_vendor_to_product(self, duplicate_product, term):
        vendor_name = None
        if term in ['Costa Interior e Assento', 'Costa Exterior', 'TECIDO CIMA', 'TECIDO BAIXO', 'Tecido']:
            vendor_name = '_fornecedor a definir'
        elif 'PINTURA' in term or term == 'ARO' or term == 'ALTERAÇÃO COR DOS PÉS':
            vendor_name = 'Alvaro José Pereira Unipessoal, Lda'

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
                _logger.warning(f"[VENDOR] Vendor '{vendor_name}' not found for product {duplicate_product.name}")"""

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
