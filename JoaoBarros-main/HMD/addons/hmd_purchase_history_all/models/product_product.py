import logging

from odoo import fields, models

from .product_template import _sanitize_purchase_history_action
from .product_template import _prepare_purchase_orders_action


_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = "product.product"

    hmd_purchase_rfq_count = fields.Integer(
        string="RFQs",
        compute="_compute_hmd_purchase_rfq_count",
    )

    def action_view_po(self):
        """Ensure variant purchase history keeps every purchase order state visible."""

        self.ensure_one()
        _logger.info(
            "Calling product.product.action_view_po for variant %s (id=%s)",
            self.display_name,
            self.id,
        )
        action = super().action_view_po()
        _logger.info(
            "Super purchase history action for variant %s returned domain=%s, context=%s",
            self.display_name,
            action.get("domain") if action else None,
            action.get("context") if action else None,
        )
        return _sanitize_purchase_history_action(self, action)

    def _compute_hmd_purchase_rfq_count(self):
        if not self.ids:
            for product in self:
                product.hmd_purchase_rfq_count = 0
            return

        group_data = self.env["purchase.order.line"].read_group(
            [("product_id", "in", self.ids)],
            ["product_id", "order_id:count_distinct"],
            ["product_id"],
        )
        counts = {
            data["product_id"][0]: data.get("order_id_count_distinct", 0)
            for data in group_data
            if data.get("product_id")
        }

        for product in self:
            product.hmd_purchase_rfq_count = counts.get(product.id, 0)

    def action_view_rfq_purchase_orders(self):
        self.ensure_one()
        return _prepare_purchase_orders_action(self, self.ids)
