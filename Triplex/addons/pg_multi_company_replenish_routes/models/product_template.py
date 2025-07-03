from odoo import models, api, _
import logging

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def create(self, vals):
        """
        Override the create method to automatically assign routes or reordering rules
        to newly created shared products.
        """
        template = super(ProductTemplate, self).create(vals)
        _logger.info("Creating reordering rules for new product: %s", template.name)
        self._create_reordering_rules_for_shared_products(template)
        return template

    def _create_reordering_rules_for_shared_products(self, templates):
        """
        Automatically creates or reactivates reordering rules for shared products (company_id = False).
        """
        # Ensure `templates` is a recordset
        templates = self.browse(templates.ids)

        # Define warehouse and route IDs
        TRIPLEX_WAREHOUSE_ID = 1  # Warehouse ID for Triplex
        OFICINNA_WAREHOUSE_ID = 2  # Warehouse ID for Oficinna
        BUY_ROUTE_ID = 5  # Buy route ID
        MANUFACTURE_ROUTE_ID = 9  # Manufacture route ID

        # Fetch warehouses explicitly by ID using sudo() to bypass access rules
        triplex_warehouse = self.env['stock.warehouse'].sudo().browse(TRIPLEX_WAREHOUSE_ID)
        oficinna_warehouse = self.env['stock.warehouse'].sudo().browse(OFICINNA_WAREHOUSE_ID)

        # Log warehouse details
        _logger.info("Triplex Warehouse: %s", triplex_warehouse.name or "Not Found")
        _logger.info("Oficinna Warehouse: %s", oficinna_warehouse.name or "Not Found")

        # Filter shared templates (company_id is False)
        shared_templates = templates.filtered(lambda t: not t.company_id)
        _logger.info("Shared templates to process: %d", len(shared_templates))

        for template in shared_templates:
            for variant in template.product_variant_ids:
                _logger.info("Processing variant: %s (ID: %d)", variant.name, variant.id)

                # Check existing rules for Triplex
                triplex_rules = self.env['stock.warehouse.orderpoint'].sudo().search([
                    ('product_id', '=', variant.id),
                    ('warehouse_id', '=', triplex_warehouse.id)
                ])
                triplex_inactive_rules = triplex_rules.filtered(lambda r: not r.active)

                # Check existing rules for Oficinna
                oficinna_rules = self.env['stock.warehouse.orderpoint'].sudo().search([
                    ('product_id', '=', variant.id),
                    ('warehouse_id', '=', oficinna_warehouse.id)
                ])
                oficinna_inactive_rules = oficinna_rules.filtered(lambda r: not r.active)

                # Reactivate inactive rules for Triplex
                if triplex_inactive_rules:
                    _logger.info("Reactivating %d inactive reordering rules for Triplex", len(triplex_inactive_rules))
                    triplex_inactive_rules.sudo().write({'active': True})

                # Create rule for Triplex if no active rule exists
                if not triplex_rules.filtered(lambda r: r.active):
                    _logger.info("Creating reordering rule for Triplex for variant %s", variant.name)
                    self.env['stock.warehouse.orderpoint'].sudo().create({
                        'product_id': variant.id,
                        'location_id': triplex_warehouse.lot_stock_id.id,  # Stock location
                        'warehouse_id': triplex_warehouse.id,
                        'company_id': triplex_warehouse.company_id.id,
                        'route_id': BUY_ROUTE_ID,  # Assign Buy route
                        'product_min_qty': 0,
                        'product_max_qty': 10,
                    })

                # Reactivate inactive rules for Oficinna
                if oficinna_inactive_rules:
                    _logger.info("Reactivating %d inactive reordering rules for Oficinna", len(oficinna_inactive_rules))
                    oficinna_inactive_rules.sudo().write({'active': True})

                # Create rule for Oficinna if no active rule exists
                if not oficinna_rules.filtered(lambda r: r.active):
                    _logger.info("Creating reordering rule for Oficinna for variant %s", variant.name)
                    self.env['stock.warehouse.orderpoint'].sudo().create({
                        'product_id': variant.id,
                        'location_id': oficinna_warehouse.lot_stock_id.id,  # Stock location
                        'warehouse_id': oficinna_warehouse.id,
                        'company_id': oficinna_warehouse.company_id.id,
                        'route_id': MANUFACTURE_ROUTE_ID,  # Assign Manufacture route
                        'product_min_qty': 0,
                        'product_max_qty': 10,
                    })


    @api.model
    def add_routes_to_existing_templates(self):
        """
        Adds or reactivates reordering rules for all existing shared product templates (company_id = False).
        """
        # Fetch all product templates
        all_templates = self.search([])
        _logger.info("Processing all existing templates: %d templates found.", len(all_templates))
        self._create_reordering_rules_for_shared_products(all_templates)

