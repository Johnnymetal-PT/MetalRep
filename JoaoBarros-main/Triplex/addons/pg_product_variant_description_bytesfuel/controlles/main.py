from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.variant import WebsiteSaleVariantController
import logging

_logger = logging.getLogger(__name__)

class VariantControllerPackage(WebsiteSaleVariantController):

    @http.route()
    def get_combination_info_website(self, product_template_id, product_id, combination, add_qty, parent_combination=None, **kwargs):
        _logger.info('Entering get_combination_info_website: product_template_id=%s, product_id=%s, combination=%s, add_qty=%s', 
                     product_template_id, product_id, combination, add_qty)
                     
        res = super().get_combination_info_website(product_template_id, product_id, combination, add_qty, parent_combination, **kwargs)
        
        if 'product_id' in res:
            product = request.env['product.product'].browse(int(res['product_id']))
            res['product_variant_desc'] = product.product_variant_desc
            _logger.info('Fetched product variant description: %s', res['product_variant_desc'])
        else:
            _logger.warning('No product_id found in response: %s', res)

        return res

