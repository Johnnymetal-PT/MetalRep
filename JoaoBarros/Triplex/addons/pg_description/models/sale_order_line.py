import re
from odoo import models, fields, api
import logging
from markupsafe import Markup

_logger = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    cart_processed_description = fields.Html(
        string="Cart Processed Description",
        compute="_compute_cart_processed_description",
        store=True,
    )

    @api.model
    def create(self, vals):
        """
        Apply description processing during the creation of sale order lines.
        """
        if 'name' in vals and vals['name']:
            _logger.info(f"Before processing name during create: {vals['name']}")
            vals['name'] = self._process_name_field(vals['name'])
            _logger.info(f"After processing name during create: {vals['name']}")
        return super(SaleOrderLine, self).create(vals)

    def write(self, vals):
        """
        Apply description processing during updates to sale order lines.
        """
        if 'name' in vals and vals['name']:
            _logger.info(f"Before processing name during write: {vals['name']}")
            vals['name'] = self._process_name_field(vals['name'])
            _logger.info(f"After processing name during write: {vals['name']}")
        return super(SaleOrderLine, self).write(vals)

    @api.depends('name', 'product_template_id')
    def _compute_cart_processed_description(self):
        """
        Compute the processed description for the cart page.
        """
        for line in self:
            if line.name and line.name != "Standard":
                _logger.info(f"Processing cart description for line: {line.name}")
                processed_description = self._process_name_field(line.name)

                # Add line breaks for cart readability
                terms = [
                    "ACABAMENTO:",
                    "PINTURA:",
                    "TECIDO 1:",
                    "TECIDO 2:",
                    "TECIDO 3:",
                    "TECIDO CIMA:",
                    "TECIDO BAIXO:",
                    "ARO:",
                    'ALTERAÇÃO COR DOS PÉS:',
                    'TIPO DE PÉ:'
                    'DIMENSÕES DO COLCHÃO:',
                    'FURAÇÃO PARA TOMADA COM CAIXA CERTIFICADA:'
                ]
                for term in terms:
                    processed_description = processed_description.replace(term, f"<br/>{term}")

                # Remove the product name for cart description
                if line.product_template_id.name:
                    processed_description = processed_description.replace(line.product_template_id.name, "").strip()

                line.cart_processed_description = Markup(processed_description)
            else:
                line.cart_processed_description = ""

    @api.onchange('name')
    def _onchange_name_process(self):
        """
        Apply processing logic when modifying the name field manually.
        """
        for line in self:
            if line.name:
                _logger.info(f"Before processing name during onchange: {line.name}")
                line.name = self._process_name_field(line.name)
                _logger.info(f"After processing name during onchange: {line.name}")

    def _process_name_field(self, name):
        """
        Shared processing logic for cleaning and formatting the description.
        """
        try:
            _logger.info(f"Processing name field: {name}")
    
            # Terms that should NOT appear at the end
            excluded_terms = {
                'Categoria A', 'Categoria B', 'Categoria C', 'Categoria D', 'Categoria E', 
                'Cliente', 'Cat. A', 'Cat. B', 'Cat. C', 'Cat. D', 'Cat. E', 'Matte',
                'Brilho | Lacado ou Verniz', 'Mesmo Tecido', 'Sem', 'Sem Ponteiras'  # Also remove "Mesmo Tecido"
            }
    
            if not name:  # Ensure 'name' is not None or empty
                _logger.warning("Name field is empty or None, returning empty string.")
                return ""
    
            # Step 1: Extract all information inside brackets BEFORE removing them
            bracketed_info = re.findall(r'\((.*?)\)', name)
            _logger.info(f"Extracted bracketed information: {bracketed_info}")
    
            # Step 2: **Split bracketed terms into individual words and filter them**
            valid_bracketed_terms = []
            for bracketed in bracketed_info:
                terms = [term.strip() for term in bracketed.split(",")]  # Split by comma
                filtered_terms = [term for term in terms if term not in excluded_terms]
                valid_bracketed_terms.extend(filtered_terms)  # Keep only valid terms
    
            _logger.info(f"Filtered valid bracketed terms: {valid_bracketed_terms}")
    
            # Step 3: Remove text inside brackets from the name
            name = re.sub(r'\(.*?\)', '', name).strip()
    
            # Handle 'TECIDO COSTAS FRENTE + ASSENTO' logic
            if 'TECIDO COSTAS FRENTE + ASSENTO' in name and 'TECIDO COSTAS TRÁS' not in name:
                name = name.replace('TECIDO COSTAS FRENTE + ASSENTO', 'TECIDO')
    
            # Handle 'TECIDO CIMA' and 'TECIDO BAIXO' logic
            if 'TECIDO CIMA' in name and 'TECIDO BAIXO' not in name:
                name = name.replace('TECIDO CIMA', 'TECIDO')
    
            # Step 4: Process remaining name text
            processed_name_lines = name.split("\n")
    
            # Step 5: Filter out excluded terms from the main text
            valid_terms = [line.strip() for line in processed_name_lines if line.strip() and line.strip() not in excluded_terms]
    
            # Step 6: Append **only the valid bracketed terms** at the end
            final_processed_name = "\n".join(valid_terms + valid_bracketed_terms).strip()
    
            _logger.info(f"Final processed name: {final_processed_name}")
            return final_processed_name
        except Exception as e:
            _logger.error(f"Error processing name field: {e}", exc_info=True)
            return name  # Return original name if an error occurs

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection(
        selection_add=[('automation_trigger', 'Automation Trigger')],
        ondelete={'automation_trigger': 'set null'},
    )

    def write(self, vals):
        """
        Override the write method to trigger name processing when the state changes.
        """
        result = super(SaleOrder, self).write(vals)

        # Check if the state is changing
        if 'state' in vals:
            _logger.info(f"State change detected for Sale Order {self.name}: {vals['state']}")

            # Process lines when the quotation changes state
            for order in self:
                if order.state in ['sent', 'sale']:
                    _logger.info(f"Processing descriptions for Sale Order {order.name}.")
                    for line in order.order_line:
                        # Process the name field
                        original_name = line.name
                        processed_name = line._process_name_field(original_name)
                        if processed_name != original_name:
                            _logger.info(f"Updating line ID {line.id} name from '{original_name}' to '{processed_name}'")
                            line.name = processed_name

        return result

