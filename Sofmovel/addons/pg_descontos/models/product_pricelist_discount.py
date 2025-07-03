from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class ProductPricelistDiscount(models.Model):
    _inherit = 'product.template'

    @api.model
    def apply_discount_tag(self):
        """
        This method:
        - Adds or removes the 'Desconto' tag and assigns ribbon with ID 5 based on 'Descontos' pricelist or if `compare_list_price` > `list_price`.
        - Ensures `compare_list_price` is updated to match `x_studio_preo_antes_desconto` when `x_studio_preo_antes_desconto` is not 0.
        """
        # Search for the 'Descontos' pricelist
        pricelist = self.env['product.pricelist'].search([('name', 'ilike', 'Desconto')], limit=1)

        if not pricelist:
            _logger.warning("Pricelist 'Descontos' not found.")
            return

        # Ensure 'Desconto' tag exists
        tag = self.env['product.tag'].search([('name', '=', 'Desconto')], limit=1)
        if not tag:
            tag = self.env['product.tag'].create({'name': 'Desconto'})
            _logger.info("Created product tag: 'Desconto'")

        # Use ribbon with ID 5
        ribbon_id = 5

        # Get all products currently in the 'Descontos' pricelist
        products_in_pricelist = set()
        pricelist_items = self.env['product.pricelist.item'].search([('pricelist_id', '=', pricelist.id)])

        for item in pricelist_items:
            product = item.product_tmpl_id or item.product_id.product_tmpl_id
            if product:
                products_in_pricelist.add(product.id)

        # Synchronize `compare_list_price` to always match `x_studio_preo_antes_desconto`
        products = self.sudo().search([])  # Use sudo to bypass any permission issues
        for product in products:
            _logger.debug(f"Product: {product.name}, x_studio_preo_antes_desconto: {product.x_studio_preo_antes_desconto}, compare_list_price: {product.compare_list_price}")
            product.sudo().write({
                'compare_list_price': product.x_studio_preo_antes_desconto or 0
            })
            _logger.info(f"Force-updated `compare_list_price` to match `x_studio_preo_antes_desconto` for product: {product.name}")

        # Search all products with the 'Desconto' tag or ribbon
        products_with_tag_or_ribbon = self.search([
            '|',
            ('product_tag_ids', 'in', tag.id),
            ('website_ribbon_id', '=', ribbon_id)
        ])

        # Remove the tag and ribbon from products not in the pricelist and not meeting the compare_list_price condition
        for product in products_with_tag_or_ribbon:
            if product.id not in products_in_pricelist and product.compare_list_price <= product.list_price:
                product.write({
                    'product_tag_ids': [(3, tag.id)],
                    'website_ribbon_id': False
                })
                _logger.info(f"Removed 'Desconto' tag and ribbon from product: {product.name}")

        # Add the tag and ribbon to products in the pricelist or if compare_list_price > list_price
        for product_id in products_in_pricelist:
            product = self.browse(product_id)
            vals = {}
            if tag not in product.product_tag_ids:
                vals.setdefault('product_tag_ids', []).append((4, tag.id))
            if product.website_ribbon_id != ribbon_id:
                vals['website_ribbon_id'] = ribbon_id
            if vals:
                product.write(vals)
                _logger.info(f"Applied 'Desconto' tag and ribbon to product: {product.name}")

        # Add the tag and ribbon to products where compare_list_price > list_price
        for product in self.search([]):
            if product.compare_list_price > product.list_price:
                vals = {}
                if tag not in product.product_tag_ids:
                    vals.setdefault('product_tag_ids', []).append((4, tag.id))
                if product.website_ribbon_id != ribbon_id:
                    vals['website_ribbon_id'] = ribbon_id
                if vals:
                    product.write(vals)
                    _logger.info(f"Applied 'Desconto' tag and ribbon to product: {product.name} (compare_list_price > list_price)")

