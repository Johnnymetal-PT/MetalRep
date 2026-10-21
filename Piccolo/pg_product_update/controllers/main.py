# controllers/main.py
"""Endpoint HTTP que dispara o walker de pastas do catalogo.

Acesso: autenticado (`auth='user'`); rota nao listada em menu, e
chamada via URL direta `/update_products` ou via botao no backoffice.
"""
from odoo import http
from odoo.http import request


class ProductUpdateController(http.Controller):
    @http.route('/update_products', type='http', auth='user', website=True)
    def update_products(self):
        # Sem confirmacao adicional: a chamada GET corre o walker.
        # E sincrono - browser fica a pendurar ate o walker terminar.
        # Em catalogo grande, considerar disparar em background.
        request.env['product.update'].update_products()
        return "Products updated successfully!"
