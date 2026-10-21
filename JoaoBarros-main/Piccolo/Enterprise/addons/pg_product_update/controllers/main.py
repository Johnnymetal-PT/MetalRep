# controllers/main.py
from odoo import http
from odoo.http import request

class ProductUpdateController(http.Controller):
    @http.route('/update_products', type='http', auth='user', website=True)
    def update_products(self):
        request.env['product.update'].update_products()
        return "Products updated successfully!"

