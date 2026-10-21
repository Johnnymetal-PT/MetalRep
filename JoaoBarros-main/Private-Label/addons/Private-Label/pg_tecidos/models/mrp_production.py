import logging
import re
import unicodedata

from odoo import _, fields, api, models
from odoo.tools import float_is_zero

_logger = logging.getLogger(__name__)

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    TERM_NAMES = [
        'WOOD',
        'FRONT WOOD',
        'INTERIOR',
        'BASE',
        'GAVETA',
        'METAL',
        'SUPORTES',
        'ESTRUTURA',
        'MÁRMORE',
        'BOTTOM WOOD',
        'TOP WOOD',
        'TAMPO',
        'TOP',
        'VIDRO',
        'FABRIC USED IN INTERNAL BACK AND SEAT',
        'FABRIC USED IN SEAT',
        'FABRIC USED IN BOTTOM OF THE SEAT',
        'FABRIC USED IN SEAT AND ARMREST',
        'FABRIC USED IN THE STRAP',
        'FABRIC USED IN ROLL',
        'FABRIC USED IN DOUBLE HEADBOARD',
        'FABRIC USED IN EXTERNAL BACK',
        'FABRIC USED IN SEAT AND CUSHION BACK',
        'FABRIC USED IN BACK AND ARMREST',
        'FABRIC USED IN BACK',
        'FABRIC USED IN BACK AND BOTTOM OF THE SEAT',
        'FABRIC USED IN UNDER SEAT AND OUTER BACK',
        'FABRIC USED IN INNER BACK; SEAT AND ARMREST',
        'FABRIC USED IN SEAT AND BACKREST',
        'FABRIC USED IN BACKREST',
        'FABRIC:',
        'MAIN FABRIC',
        'FABRIC USED IN CUSTOM',
        'DIMENSIONS',
    ]

    BOM_TERMS = [term for term in TERM_NAMES if term != 'DIMENSIONS']

    TERM_BASE_MAP = {
        'WOOD': 'WOOD',
        'FRONT WOOD': 'WOOD',
        'BOTTOM WOOD': 'WOOD',
        'TOP WOOD': 'WOOD',
    }

    @classmethod
    def _get_base_term(cls, term):
        """Return the normalized base term used for precedence checks."""
        normalized = (term or '').strip().upper()
        if not normalized:
            return ''

        if normalized in cls.TERM_BASE_MAP:
            return cls.TERM_BASE_MAP[normalized]

        if normalized in cls.TERM_NAMES:
            return normalized

        for candidate in cls.TERM_NAMES:
            candidate_upper = (candidate or '').strip().upper()
            if candidate_upper and normalized.startswith(f"{candidate_upper} "):
                return cls.TERM_BASE_MAP.get(candidate_upper, candidate_upper)

        return normalized

    TERM_DEFINITIONS = [
        ('FRONT WOOD', ['front wood']),
        ('BOTTOM WOOD', ['bottom wood']),
        ('TOP WOOD', ['top wood']),
        ('TAMPO', ['tampo']),
        ('WOOD', ['wood']),
        ('INTERIOR', ['interior']),
        ('BASE', ['base']),
        ('GAVETA', ['gaveta', 'gavetas']),
        ('METAL', ['metal']),
        ('SUPORTES', ['suportes', 'suporte']),
        ('ESTRUTURA', ['estrutura']),
        ('MÁRMORE', ['mármore', 'marmore']),
        ('TOP', ['top']),
        ('VIDRO', ['vidro']),
        ('FABRIC USED IN INTERNAL BACK AND SEAT', ['fabric used in internal back and seat']),
        ('FABRIC USED IN SEAT', ['fabric used in seat']),
        ('FABRIC USED IN BOTTOM OF THE SEAT', ['fabric used in bottom of the seat']),
        ('FABRIC USED IN SEAT AND ARMREST', ['fabric used in seat and armrest']),
        ('FABRIC USED IN THE STRAP', ['fabric used in the strap']),
        ('FABRIC USED IN ROLL', ['fabric used in roll']),
        ('FABRIC USED IN DOUBLE HEADBOARD', ['fabric used in double headboard']),
        ('FABRIC USED IN EXTERNAL BACK', ['fabric used in external back']),
        ('FABRIC USED IN SEAT AND CUSHION BACK', ['fabric used in seat and cushion back']),
        ('FABRIC USED IN BACK AND ARMREST', ['fabric used in back and armrest']),
        ('FABRIC USED IN BACK', ['fabric used in back']),
        ('FABRIC USED IN BACK AND BOTTOM OF THE SEAT', ['fabric used in back and bottom of the seat']),
        ('FABRIC USED IN UNDER SEAT AND OUTER BACK', ['fabric used in under seat and outer back']),
        ('FABRIC USED IN INNER BACK; SEAT AND ARMREST', ['fabric used in inner back; seat and armrest']),
        ('FABRIC USED IN SEAT AND BACKREST', ['fabric used in seat and backrest']),
        ('FABRIC USED IN BACKREST', ['fabric used in backrest']),
        ('FABRIC:', ['fabric:']),
        ('MAIN FABRIC', ['main fabric']),
        ('FABRIC USED IN CUSTOM', ['fabric used in custom']),
    ]

    SPECIAL_LABELS = {
        'WOOD': [
            'Estrutura e Polimento',
            'Casco',
            'Polimento',
            'Rodapé',
            'Madeira',
            'Casco, Polimento e Estofo',
            'Madeira, Polimento e Estofo',
            'Pormenores Braços',
            'Base e Polimento',
            'Madeira e Polimento',
            'Friso e Polimento',
        ],
        'FRONT WOOD': ['Estrutura e Polimento'],
        'INTERIOR': ['Estrutura e Polimento'],
        'BASE': ['Estrutura e Polimento'],
        'GAVETA': ['Estrutura e Polimento'],
        'BOTTOM WOOD': ['Estrutura e Polimento'],
        'TOP WOOD': ['Estrutura e Polimento'],
        'METAL': ['Apoio Costa'],
        'SUPORTES': ['Metal'],
        'ESTRUTURA': ['Metal'],
        'MÁRMORE': ['Marble'],
        'TAMPO': ['Tampo'],
        'TOP': ['Tampo'],
        'VIDRO': ['Tampo'],
        'MAIN FABRIC': [
            'Casco e Estofo',
            'Casco, Polimento e Estofo',
            'Estrutura, Polimento e Estofo',
            'Madeira, Polimento e Estofo',
        ],
    }

    TERM_PRIORITY = {term: index for index, term in enumerate(TERM_NAMES)}

    product_description_variants = fields.Char()
    partner_id = fields.Many2one(
        'res.partner',
        string='Fornecedor',
        domain="['|', ('company_id', '=', company_id), ('company_id', 'parent_of', company_id)]",
    )

    def _get_zero_quantity_components(self):
        default_rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure') or 0.0001
        zero_moves = self.move_raw_ids.filtered(
            lambda move: float_is_zero(
                move.product_uom_qty,
                precision_rounding=(move.product_uom and move.product_uom.rounding) or default_rounding,
            )
        )
        return zero_moves.filtered(lambda move: move.product_id)

    def _format_zero_qty_message(self, zero_moves):
        message_lines = []
        for production in self:
            moves = zero_moves.filtered(lambda move: move.raw_material_production_id == production)
            if not moves:
                continue
            products = ', '.join(moves.mapped('product_id.display_name'))
            message_lines.append(_("%s: %s") % (production.name, products))
        return '\n'.join(message_lines)

    def action_confirm(self):
        if not self.env.context.get('skip_zero_qty_warning'):
            zero_moves = self._get_zero_quantity_components()
            if zero_moves:
                return {
                    'type': 'ir.actions.act_window',
                    'name': _('Components with zero quantity'),
                    'res_model': 'mrp.production.zero.qty.warning',
                    'view_mode': 'form',
                    'target': 'new',
                    'context': {
                        'default_production_ids': self.ids,
                        'default_zero_component_message': self._format_zero_qty_message(zero_moves),
                    },
                }

        return super().action_confirm()

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

        terms = {term: '' for term in self.TERM_NAMES}

        _logger.info(f"[CREATE] Product description variants: {description}")

        normalized_description = description.replace('\r\n', '\n')

        # Extract the text for each term
        for term in terms:
            normalized_term = term.lower().rstrip(':')
            pattern = re.compile(rf"{re.escape(normalized_term)}:\s*([^\n\r,]+)", re.IGNORECASE)
            match = pattern.search(normalized_description)
            if match:
                cleaned_value = re.sub(r"\s+", " ", match.group(1)).strip(" ,")
                terms[term] = cleaned_value
                _logger.info(f"[CREATE] Extracted term '{term}': {terms[term]}")

        # Fetch "DIMENSIONS" from product variant attribute values
        sale_order_line = self.env['sale.order.line'].search([('product_id', '=', vals.get('product_id'))], limit=1)
        if sale_order_line:
            dimensions_values = sale_order_line.product_template_attribute_value_ids.filtered(
                lambda ptav: 'dimensions' in (ptav.attribute_id.name or '').lower()
            )
            if dimensions_values:
                dimensoes_value = dimensions_values[0].name
                if dimensoes_value:
                    terms['DIMENSIONS'] = dimensoes_value
                    _logger.info(f"[CREATE] Selected DIMENSIONS: {dimensoes_value}")

        # Update the product_description_variants with all terms (ensuring no duplication)
        existing_description = vals.get('product_description_variants', '').strip()

        # Parse existing terms into a dictionary
        existing_terms = {}
        if existing_description:
            normalized_existing = existing_description.replace('\r\n', '\n')
            for item in re.split(r',\s*|\n+', normalized_existing):
                if ': ' in item:
                    key, value = item.split(': ', 1)
                    existing_terms[key.strip()] = re.sub(r"\s+", " ", value).strip()

        # Build a map of detected base terms present in the existing description
        existing_bases = {}
        for existing_key in existing_terms:
            base_term = self._get_base_term(existing_key)
            existing_bases.setdefault(base_term, []).append(existing_key)

        # Merge existing terms with new terms
        for term, value in terms.items():
            if value:  # Only update terms with a non-empty value
                base_term = self._get_base_term(term)
                term_upper = term.upper()
                base_keys = existing_bases.get(base_term, [])
                has_specific = any(key.upper() != term_upper for key in base_keys)

                if has_specific:
                    _logger.info(
                        f"[CREATE] Skipping base term '{term}' because specific variants {base_keys} already exist."
                    )
                    continue

                existing_terms[term] = value
                if term not in base_keys:
                    existing_bases.setdefault(base_term, []).append(term)

        # Rebuild the product_description_variants field
        vals['product_description_variants'] = ', '.join(f"{key}: {value}" for key, value in existing_terms.items())
        _logger.info(f"[CREATE] Final product_description_variants: {vals['product_description_variants']}")

        product_qty = sale_order_line.product_uom_qty if sale_order_line else 1

        # Step 1: Search the oldest BoM for the product
        oldest_bom = self._search_oldest_bom(vals.get('product_id'))

        # Step 2: Duplicate the BoM (prevent modifying the oldest BoM)
        duplicated_bom = self._duplicate_bom(oldest_bom, product_qty)

        # Only apply consumption values if duplicated_bom is not None
        if duplicated_bom:
            # Step 3: Map the duplicated BoM lines to the detected terms and extracted texts
            line_matches = self._map_terms_to_bom_lines(duplicated_bom, terms)

            # Step 4: Update the duplicated BoM lines with consumption values before assigning duplicated products
            self._apply_consumption_values(duplicated_bom, line_matches, product_qty)

            # Step 5: Duplicate products based on terms and update the duplicated BoM
            self._duplicate_and_assign_to_bom(duplicated_bom, line_matches, terms)

        # Step 6: Create the Manufacturing Order
        vals['state'] = 'draft'
        production = super(MrpProduction, self).create(vals)
        if duplicated_bom:
            production.write({'bom_id': duplicated_bom.id})
            _logger.info(f"[CREATE] Assigned duplicated BoM {duplicated_bom.id} to Manufacturing Order {production.id}")

        return production

    def _search_oldest_bom(self, product_id):
        product = self.env['product.product'].browse(product_id)
        bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', product.product_tmpl_id.id)], order='create_date asc', limit=1)
        _logger.info(f"[BOM] Found oldest BoM for product {product.product_tmpl_id.id}: {bom.id if bom else 'No BoM found'}")
        return bom

    def _duplicate_bom(self, bom, product_qty):
        if bom:
            duplicated_bom = bom.copy()
            _logger.info(f"[BOM] Duplicated BoM {bom.id} to new BoM {duplicated_bom.id}")

            if duplicated_bom.product_qty != product_qty:
                duplicated_bom.product_qty = product_qty
                _logger.info(f"[BOM] Updated duplicated BoM product_qty to {product_qty}")

            # Update product quantities in the duplicated BoM lines
            for line in duplicated_bom.bom_line_ids:
                product_name = line.product_id.name

                term_in_line, _keyword = self._identify_term(product_name)
                component_uom = line.product_uom_id or line.product_id.uom_id
                is_fabric_component = (
                    term_in_line
                    and 'FABRIC' in term_in_line
                    and self._is_fabric_uom(component_uom)
                )

                if not is_fabric_component:
                    original_qty = line.product_qty
                    scaled_qty = original_qty * product_qty
                    line.product_qty = scaled_qty
                    _logger.info(
                        "[BOM] Scaled component %s: Original Qty %s, New Qty %s",
                        line.product_id.name,
                        original_qty,
                        scaled_qty,
                    )
                else:
                    _logger.info(
                        "[BOM] Skipping fabric component %s in bulk scaling step; will be set from consumption table.",
                        line.product_id.name,
                    )

            return duplicated_bom
        return None

    def _apply_consumption_values(self, bom, line_matches, product_qty):
        """
        Apply the appropriate consumption values to BoM lines in the duplicated BoM
        based on the original component/material in the original BoM.
        """
        if not bom:
            return

        for line in bom.bom_line_ids:
            line_data = line_matches.get(line.id)
            if not line_data:
                _logger.info(
                    f"[BOM] Skipping BoM line product {line.product_id.id}, as it doesn't match specified terms (sanitized name: '{self._strip_bracket_content(line.product_id.name)}')."
                )
                continue

            term = line_data['primary_term']
            if term not in self.BOM_TERMS:
                _logger.info(f"[BOM] Skipping BoM line product {line.product_id.id}, as it doesn't match specified terms.")
                continue

            replacements = [item for item in line_data.get('replacements', []) if item[1]]
            component_uom = line.product_uom_id or line.product_id.uom_id
            is_fabric_term = any('FABRIC' in replacement_term for replacement_term, _value in replacements)
            is_fabric_uom = self._is_fabric_uom(component_uom)

            # Apply the consumption value if the term matches
            component_template = line.product_id.product_tmpl_id  # Component in the BoM line

            if not is_fabric_term or not is_fabric_uom:
                _logger.info(
                    f"[BOM] Retaining original quantity for line {line.id} (term '{term}'): "
                    f"Component: {component_template.name}, Product Qty: {line.product_qty}"
                )
                continue

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

    def _duplicate_and_assign_to_bom(self, bom, line_matches, term_values):
        if not bom:
            return

        for line in bom.bom_line_ids:
            line_data = line_matches.get(line.id)
            if not line_data:
                continue

            term = line_data['primary_term']
            if term == 'DIMENSIONS':
                _logger.info("[DUPLICATE] Term 'DIMENSIONS' detected, skipping duplication for BoM components.")
                continue

            replacements = [(replacement_term, value) for replacement_term, value in line_data.get('replacements', []) if value]
            combined_replacement = self._combine_replacements(term, replacements)
            if not combined_replacement:
                continue

            original_variant = line.product_id
            product = original_variant.product_tmpl_id
            _logger.info(
                f"[DUPLICATE] Found product variant for '{term}' in BoM: "
                f"{original_variant.id} - {original_variant.display_name}"
            )

            component_uom = line.product_uom_id or line.product_id.uom_id
            is_fabric_uom = self._is_fabric_uom(component_uom)
            duplicate_name = self._build_duplicate_name(
                product.name,
                combined_replacement,
                term,
                is_fabric_uom=is_fabric_uom,
            )
            if not self._is_fabric_term(term):
                duplicate_name = self._append_dimensions_term(
                    duplicate_name,
                    (term_values or {}).get('DIMENSIONS'),
                )
            _logger.info(f"[DUPLICATE] Generated duplicate name '{duplicate_name}' for term '{term}'")

            duplicate_variant = self._get_or_create_duplicate_variant(original_variant, duplicate_name, term)

            line.write({'product_id': duplicate_variant.id})
            _logger.info(
                f"[BOM] Replaced original product {original_variant.id} with duplicated product {duplicate_variant.id} in BoM line"
            )

    def _get_or_create_duplicate_variant(self, original_variant, duplicate_name, term):
        ProductVariant = self.env['product.product'].with_context(active_test=False)
        original_attribute_ids = set(original_variant.product_template_attribute_value_ids.ids)

        existing_variants = ProductVariant.search([('name', '=', duplicate_name)], order="active desc, create_date desc")
        if existing_variants:
            for variant in existing_variants:
                if variant.active and set(variant.product_template_attribute_value_ids.ids) == original_attribute_ids:
                    _logger.info(
                        "[DUPLICATE] Product variant '%s' already exists with matching attributes, using variant ID: %s",
                        duplicate_name,
                        variant.id,
                    )
                    return variant

            for variant in existing_variants:
                if variant.active:
                    _logger.info(
                        "[DUPLICATE] Active product variant '%s' already exists, reusing variant ID: %s",
                        duplicate_name,
                        variant.id,
                    )
                    return variant

            for variant in existing_variants:
                if set(variant.product_template_attribute_value_ids.ids) == original_attribute_ids:
                    variant.write({'active': True})
                    _logger.info(
                        "[DUPLICATE] Reactivated matching product variant '%s' with ID: %s",
                        duplicate_name,
                        variant.id,
                    )
                    return variant

            chosen_variant = existing_variants[0]
            if not chosen_variant.active:
                chosen_variant.write({'active': True})
            _logger.info(
                "[DUPLICATE] Reusing existing product variant '%s' with ID: %s despite attribute differences.",
                duplicate_name,
                chosen_variant.id,
            )
            return chosen_variant

        original_template = original_variant.product_tmpl_id
        duplicate_template = original_template.copy()
        duplicate_template.name = duplicate_name

        duplicate_variant = self._match_variant_by_attributes(
            duplicate_template.product_variant_ids,
            original_attribute_ids,
        )
        if not duplicate_variant:
            duplicate_variant = duplicate_template.product_variant_id

        duplicate_variant.name = duplicate_name
        if original_attribute_ids:
            duplicate_variant.write({
                'product_template_attribute_value_ids': [(6, 0, list(original_attribute_ids))],
            })

        self._copy_custom_fields(original_template, duplicate_template)
        self._copy_supplierinfo(
            original_template,
            duplicate_template,
            original_variant=original_variant,
            duplicate_variant=duplicate_variant,
        )
        self._copy_variant_fields(original_variant, duplicate_variant)

        _logger.info(f"[DUPLICATE] Created new product variant: {duplicate_variant.display_name}")

        self._assign_vendor_to_product(duplicate_template, term)

        return duplicate_variant

    @staticmethod
    def _match_variant_by_attributes(variants, attribute_ids):
        attribute_ids = set(attribute_ids or [])
        for variant in variants:
            if set(variant.product_template_attribute_value_ids.ids) == attribute_ids:
                return variant
        fallback = variants[:1]
        return fallback if fallback else variants

    def _copy_variant_fields(self, original_variant, duplicate_variant):
        fields_to_copy = ['default_code', 'barcode']
        values_to_write = {}
        for field in fields_to_copy:
            if hasattr(original_variant, field):
                value = getattr(original_variant, field)
                if value:
                    values_to_write[field] = value

        if values_to_write:
            duplicate_variant.write(values_to_write)

    def _append_dimensions_term(self, name, dimensions_value):
        cleaned_dimensions = re.sub(r"\s+", " ", (dimensions_value or '')).strip(" ,")
        if not cleaned_dimensions:
            return name

        suffix = self._extract_suffix(name)
        base_name = name[:-len(suffix)] if suffix else name

        dimension_segment = f"DIMENSIONS: {cleaned_dimensions}"
        if dimension_segment in base_name:
            return name

        if base_name:
            if base_name.endswith(','):
                base_with_dimensions = f"{base_name} {dimension_segment}"
            else:
                base_with_dimensions = f"{base_name}, {dimension_segment}" if dimension_segment not in base_name else base_name
        else:
            base_with_dimensions = dimension_segment

        return self._append_suffix(base_with_dimensions, suffix)

    def _assign_vendor_to_product(self, duplicate_product, term):
        vendor_name = None

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

    def _copy_supplierinfo(self, original_product, duplicate_product, original_variant=None, duplicate_variant=None):
        supplier_infos = original_product.seller_ids
        if not supplier_infos:
            return

        for supplier_info in supplier_infos:
            supplier_product_id = False
            if original_variant and duplicate_variant and supplier_info.product_id:
                if supplier_info.product_id.id == original_variant.id:
                    supplier_product_id = duplicate_variant.id
            values = {
                'product_tmpl_id': duplicate_product.id,
                'product_id': supplier_product_id,
                'partner_id': supplier_info.partner_id.id,
                'min_qty': supplier_info.min_qty,
                'price': supplier_info.price,
                'currency_id': supplier_info.currency_id.id,
                'delay': supplier_info.delay,
                'date_start': supplier_info.date_start,
                'date_end': supplier_info.date_end,
                'product_name': supplier_info.product_name,
                'product_code': supplier_info.product_code,
                'company_id': supplier_info.company_id.id or False,
            }
            self.env['product.supplierinfo'].create(values)

    @classmethod
    def _identify_term(cls, name, term_values=None):
        matches = cls._match_terms(name, term_values)
        if not matches:
            return None, None
        term, keyword = matches[0]
        return term, keyword

    @classmethod
    def _match_terms(cls, name, term_values=None):
        sanitized_name = cls._strip_bracket_content(name)
        normalized_name = cls._normalize_text(sanitized_name)
        _logger.debug(
            "[IDENTIFY] Checking name '%s' (sanitized: '%s') for matching terms.",
            name,
            sanitized_name,
        )

        if not normalized_name:
            return []

        matches = {}

        def add_match(term, keyword, source):
            if term not in cls.TERM_PRIORITY:
                return
            score = 0
            if source == 'keyword':
                score += 3
            elif source == 'label':
                score += 2
            elif source == 'special':
                score += 1

            if term_values and term_values.get(term):
                score += 10

            order = -cls.TERM_PRIORITY.get(term, 0)
            existing = matches.get(term)
            if not existing or (score, order) > (existing[0], existing[1]):
                matches[term] = (score, order, term, keyword)

        for term, keywords in cls.TERM_DEFINITIONS:
            matched = False
            for keyword in keywords:
                normalized_keyword = cls._normalize_text(keyword)
                if cls._keyword_in_name(normalized_keyword, normalized_name):
                    add_match(term, keyword, 'keyword')
                    matched = True
                    break

            if not matched and normalized_name == cls._normalize_text(term):
                add_match(term, term, 'label')
                matched = True

            if not matched:
                for label in cls.SPECIAL_LABELS.get(term, []):
                    if normalized_name == cls._normalize_text(label):
                        add_match(term, label, 'special')
                        break

        if not matches:
            return []

        sorted_matches = sorted(matches.values(), key=lambda item: (item[0], item[1]), reverse=True)
        return [(term, keyword) for _score, _order, term, keyword in sorted_matches]

    @staticmethod
    def _keyword_in_name(keyword, name_lower):
        if not keyword or not name_lower:
            return False
        if ' ' in keyword:
            return keyword in name_lower
        return re.search(rf'\b{re.escape(keyword)}\b', name_lower) is not None

    @staticmethod
    def _normalize_text(value):
        if not value:
            return ''

        normalized = unicodedata.normalize('NFKD', value)
        stripped = ''.join(char for char in normalized if not unicodedata.combining(char))
        return stripped.lower()

    def _build_duplicate_name(self, original_name, replacement, term, is_fabric_uom=True):
        if not replacement:
            return original_name

        cleaned_replacement = re.sub(r"\s+", " ", replacement).strip()

        # For fabric components we only want the fabric name itself, without
        # any prefix from the original product or additional labels.
        if self._is_fabric_term(term):
            if not is_fabric_uom:
                return self._replace_fabric_term_in_name(original_name, term, cleaned_replacement)
            return cleaned_replacement

        suffix = self._extract_suffix(original_name)

        sanitized_name = self._strip_bracket_content(original_name)
        if sanitized_name != original_name:
            _logger.info(
                f"[DUPLICATE] Sanitized original name '{original_name}' to '{sanitized_name}' before rebuilding."
            )

        # Preserve the attribute label of the component when generating the duplicate name.
        separators = [':', '-', '–', '—']
        for separator in separators:
            if separator in sanitized_name:
                prefix, _suffix = sanitized_name.split(separator, 1)
                prefix = prefix.strip()
                if not prefix:
                    continue
                resolved_prefix = self._resolve_label(prefix, term)
                if separator == ':':
                    base = f"{resolved_prefix}: {cleaned_replacement}".strip()
                else:
                    base = f"{resolved_prefix} {separator} {cleaned_replacement}".strip()
                return self._append_suffix(base, suffix)

        # If we cannot detect a separator but the term label is already present, append the replacement.
        if term and term.lower() in (sanitized_name or '').lower():
            base_name = sanitized_name if sanitized_name else original_name
            if cleaned_replacement.lower() in base_name.lower():
                base = base_name
            else:
                base = f"{base_name} - {cleaned_replacement}"
            return self._append_suffix(base, suffix)

        # Final fallback, keep the term label visible.
        label = self._resolve_label(sanitized_name or original_name, term)
        base = f"{label}: {cleaned_replacement}"
        return self._append_suffix(base, suffix)

    @staticmethod
    def _is_fabric_uom(uom):
        if not uom:
            return False
        return (uom.name or '').strip().lower() == 'm'

    @staticmethod
    def _replace_fabric_term_in_name(original_name, term, replacement):
        if not original_name:
            return replacement

        term_label = (term or '').strip()
        if not term_label:
            return original_name

        candidate_labels = [term_label, term_label.rstrip(':').strip()]
        for label in candidate_labels:
            if not label:
                continue
            pattern = re.compile(re.escape(label), re.IGNORECASE)
            if pattern.search(original_name):
                return pattern.sub(replacement, original_name, count=1)

        return original_name

    @staticmethod
    def _is_fabric_term(term):
        return 'FABRIC' in (term or '').upper()

    @staticmethod
    def _append_suffix(base, suffix):
        if not suffix:
            return base
        if suffix.startswith(' ') or base.endswith(' '):
            return f"{base}{suffix}"
        return f"{base} {suffix}"

    @staticmethod
    def _extract_suffix(original_name):
        if not original_name:
            return ''

        matches = re.findall(r"(\s*(?:\([^)]*\)|\[[^]]*\]|\{[^}]*\}|<[^>]*>))", original_name)
        return ''.join(matches)

    def _resolve_label(self, original_label, term):
        original_label = (original_label or '').strip()
        term_label = (term or '').strip()

        if original_label and original_label.lower() != term_label.lower():
            return original_label

        special_labels = self.SPECIAL_LABELS.get(term_label, [])
        if special_labels:
            if original_label:
                for candidate in special_labels:
                    if original_label.lower() == candidate.lower():
                        return candidate
            if len(special_labels) == 1:
                return special_labels[0]

        if original_label:
            return original_label

        if special_labels:
            return special_labels[0]

        return term_label

    @staticmethod
    def _strip_bracket_content(value):
        if not value:
            return value

        sanitized = re.sub(r"\s*\([^)]*\)", "", value)
        sanitized = re.sub(r"\s*\[[^]]*\]", "", sanitized)
        sanitized = re.sub(r"\s*\{[^}]*\}", "", sanitized)
        sanitized = re.sub(r"\s*<[^>]*>", "", sanitized)
        sanitized = sanitized.strip()
        _logger.debug("[SANITIZE] Input '%s' sanitized to '%s'", value, sanitized)
        return sanitized

    def _map_terms_to_bom_lines(self, bom, term_values):
        line_matches = {}
        if not bom:
            return line_matches

        for line in bom.bom_line_ids:
            matches = self._match_terms(line.product_id.name, term_values)
            if not matches:
                sanitized_name = self._strip_bracket_content(line.product_id.name)
                _logger.info(
                    f"[BOM] Skipping BoM line product {line.product_id.id}, as it doesn't match specified terms (sanitized name: '{sanitized_name}')."
                )
                continue

            replacements = []
            for term, keyword in matches:
                extracted_text = term_values.get(term, '')
                replacements.append((term, extracted_text))
                _logger.info(f"[BOM] Extracted text for term '{term}': {extracted_text}")

            primary_term = matches[0][0]
            primary_term = self.TERM_BASE_MAP.get(primary_term, primary_term)
            line_matches[line.id] = {
                'primary_term': primary_term,
                'replacements': replacements,
            }

        return line_matches

    def _combine_replacements(self, primary_term, replacements):
        if not replacements:
            return ''

        unique_values = {}
        for term, value in replacements:
            cleaned_value = re.sub(r"\s+", " ", value or '').strip(" ,")
            if not cleaned_value:
                continue
            if term not in unique_values:
                unique_values[term] = cleaned_value

        if not unique_values:
            return ''

        base_term = self.TERM_BASE_MAP.get(primary_term, primary_term)
        has_specific = any(
            self.TERM_BASE_MAP.get(term, term) == base_term and term != base_term
            for term in unique_values
        )
        if has_specific:
            unique_values.pop(base_term, None)

        ordered_terms = sorted(unique_values.keys(), key=lambda t: self.TERM_PRIORITY.get(t, 0))
        segments = []

        if len(unique_values) == 1 and ordered_terms[0] == primary_term:
            return unique_values[ordered_terms[0]]

        for term in ordered_terms:
            segments.append(f"{term}: {unique_values[term]}")

        return ', '.join(segments)
