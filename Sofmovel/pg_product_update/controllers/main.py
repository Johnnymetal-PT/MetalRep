"""Endpoint HTTP para acionar `product.update.update_products`.

Pertence ao modulo `pg_product_update`. Rota com `auth='user'` (requer login);
util para invocar o processo via scheduler externo ou por administradores.
"""
from odoo import http
from odoo.http import request

class ProductUpdateController(http.Controller):
    """Controller HTTP simples que dispara a atualizacao em massa."""

    @http.route('/update_products', type='http', auth='user', website=True)
    def update_products(self):
        # O processo e sincrono e pode demorar; ler logs do servidor para
        # acompanhar progresso.
        request.env['product.update'].update_products()
        return "Products updated successfully!"

