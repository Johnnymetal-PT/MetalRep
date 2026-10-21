import logging

from odoo import models

from .product_template import _sanitize_purchase_history_action


_logger = logging.getLogger(__name__)


class ProductSupplierinfo(models.Model):
    _inherit = "product.supplierinfo"

    def action_purchase_history(self):
        """Relax state restrictions when opening the vendor purchase history."""

        self.ensure_one()
        _logger.info(
            "Calling product.supplierinfo.action_purchase_history for vendor record %s (id=%s)",
            self.display_name,
            self.id,
        )
        action = super().action_purchase_history()
        _logger.info(
            "Super vendor purchase history action for %s returned domain=%s, context=%s",
            self.display_name,
            action.get("domain") if action else None,
            action.get("context") if action else None,
        )
        return _sanitize_purchase_history_action(self, action)
