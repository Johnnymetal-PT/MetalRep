from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.onchange('partner_id')
    def _onchange_partner_id_filter_shipping(self):
        """
        Dynamically filter partner_shipping_id based on the selected partner_id.
        """
        if self.partner_id:
            _logger.info(f"Selected Partner: {self.partner_id.name} (ID: {self.partner_id.id})")

            # Fetch child_ids with type 'delivery'
            shipping_partners = self.partner_id.child_ids.filtered(lambda p: p.type == 'delivery')

            if shipping_partners:
                _logger.info(f"Shipping Addresses Found: {[(partner.name, partner.id) for partner in shipping_partners]}")
                domain = [('id', 'in', shipping_partners.ids)]
            else:
                # Fallback to default partner_id address
                _logger.info("No child_ids found. Falling back to the partner's default address.")
                domain = [('id', '=', self.partner_id.id)]

            _logger.info(f"Applying Domain: {domain}")

            # Explicitly return the domain to ensure it's applied
            return {
                'domain': {
                    'partner_shipping_id': domain,
                },
            }
        else:
            _logger.info("No Partner Selected. Resetting domain for partner_shipping_id.")
            return {
                'domain': {
                    'partner_shipping_id': [],
                },
            }

