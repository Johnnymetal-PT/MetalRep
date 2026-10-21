"""Bloqueia /shop a utilizadores nao autenticados (redirect para login).

Substitui a rota standard ``/shop`` por uma versao que verifica se o
utilizador e publico antes de delegar no controller do core.
"""
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteShopRedirect(http.Controller):

    @http.route(['/shop'], type='http', auth="public", website=True)
    def shop_redirect(self, **kw):
        # _is_public() devolve True para o utilizador "Public" anonimo;
        # qualquer login (mesmo portal) passa neste teste.
        if not request.env.user or request.env.user._is_public():
            return request.redirect('/web/login')
            # Alternativa: redirecionar para a homepage.
            # return request.redirect('/')

        # Utilizador autenticado - delegar no controller standard
        # WebsiteSale para preservar o comportamento original do /shop.
        return WebsiteSale().shop()
