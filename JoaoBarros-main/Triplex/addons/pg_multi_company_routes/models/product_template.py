from odoo import models, api
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        for order in self:
            company_id = order.company_id.id
            company_name = order.company_id.name
            _logger.warning(f"🔁 action_confirm() triggered for SO: {order.name} | Company: {company_name} (ID: {company_id})")

            # Define correct route names per company
            if company_id == 1:  # Triplex
                required_routes = ['Buy', 'Replenish on Order (MTO)']
            elif company_id == 2:  # Oficinna22
                required_routes = ['Manufacture', 'Replenish on Order (MTO)']
            else:
                _logger.warning(f"🚫 Unknown company ID {company_id}. Skipping route assignment.")
                continue

            # Get all routes for this company
            available_routes = self.env['stock.route'].search([
                ('name', 'in', required_routes),
                ('company_id', '=', company_id)
            ])
            route_ids = set(available_routes.ids)

            _logger.info(f"📦 Routes to enforce for company {company_name}: {required_routes} => IDs: {list(route_ids)}")

            # Process only shared products (company_id=False)
            shared_templates = order.order_line.mapped('product_id.product_tmpl_id').filtered(lambda p: not p.company_id)

            for product in shared_templates:
                old_route_ids = set(product.route_ids.ids)
                if old_route_ids != route_ids:
                    product.route_ids = [(6, 0, list(route_ids))]
                    _logger.warning(f"✅ Product '{product.name}' (ID: {product.id}) updated: {old_route_ids} → {route_ids}")
                else:
                    _logger.info(f"⏩ Product '{product.name}' already has correct routes.")

        return super().action_confirm()

