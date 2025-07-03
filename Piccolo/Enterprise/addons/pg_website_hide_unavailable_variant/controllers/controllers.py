# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.exceptions import UserError
from odoo.http import request

# This controller class handles HTTP requests related to hiding product variants on the website.
class HideVariant(http.Controller):
    
    # This route defines an endpoint accessible via JSON-RPC at the URL "/get_product_variant_data_website".
    # It's a public endpoint and accessible from the website.
    # The function `get_product_variant_data` is called when a request is made to this route.
    @http.route("/get_product_variant_data_website", type="json", website=True, auth="public")
    def get_product_variant_data(self, product_tmpl_id):
        # Fetches the product template with the specified ID.
        product_tmpl_id = request.env["product.template"].search([("id", "=", product_tmpl_id)])
        
        # If the product template exists, it returns the variant count data.
        # The function `get_variant_count` is assumed to be a method on the product template model that
        # retrieves information about the variants of this product, likely including their visibility status.
        if product_tmpl_id:
            return product_tmpl_id.get_variant_count()
        # If the product template is not found, no specific handling is done in this snippet.
        # Consider adding error handling or a meaningful response for better API design.
