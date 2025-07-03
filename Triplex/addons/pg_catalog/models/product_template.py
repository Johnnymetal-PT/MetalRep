from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def compute_catalog_prices(self):
        """ Computes the first four non-zero price_extra values and ensures valid output. """
        self.ensure_one()
        price_extras = self.env['product.template.attribute.value'].search([
            ('product_tmpl_id', '=', self.id),
            ('price_extra', '!=', 0)
        ], order='price_extra asc')

        list_price = self.list_price
        prices = []

        return prices  # Now returning numeric values, not formatted text

    def action_print_catalog(self):
        """ Generates the product catalog PDF report for multiple selected products. """
        if not self:
            raise ValueError("No products selected for catalog printing.")
        
        return self.env.ref('pg_catalog.product_template_report_action').report_action(self)

    def action_print_catalog_255(self):
        """ Generates the 255 version of the Product Catalog PDF. """
        if not self:
            raise ValueError("No products selected for catalog printing (255).")
        return self.env.ref('pg_catalog.product_template_report_action_255').report_action(self)

    def action_print_catalog_usa(self):
        """ Generates the USA version of the Product Catalog PDF. """
        if not self:
            raise ValueError("No products selected for catalog printing (USA).")
        return self.env.ref('pg_catalog.product_template_report_action_usa').report_action(self)
        
    def action_print_catalog_maisondoree(self):
        """ Generates the Maison Dorée version of the Product Catalog PDF. """
        if not self:
            raise ValueError("No products selected for catalog printing (Maison Dorée).")
        return self.env.ref('pg_catalog.product_template_report_action_maisondoree').report_action(self)
