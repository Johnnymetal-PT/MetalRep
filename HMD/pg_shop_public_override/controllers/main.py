# -*- coding: utf-8 -*-
"""Controllers HTTP do `pg_shop_public_override`.

Garante que utilizadores publicos conseguem aceder ao catalogo da HMD
sem serem forcados a iniciar sessao, e expoe duas rotas alternativas:

- `/artigos` -> catalogo simplificado pelo template QWeb
  `website.artigos` (definido fora deste modulo).
- `/smart-shop` -> redireciona dinamicamente para `/shop` ou
  `/artigos` conforme o utilizador esteja autenticado ou nao.

Ver o `__manifest__.py` para o guia completo (objetivo, FAQ e avisos).
"""

from odoo import http
from odoo.http import request
from odoo.addons.website.controllers.main import Website  # noqa: F401 - mantido por compatibilidade com extensoes futuras


class ShopPublicAccess(http.Controller):
    """Override da rota `/shop` para nao redirecionar publico para login."""

    @http.route('/shop', auth='public', website=True)
    def public_shop(self, **kwargs):
        # Hardcoded: 302 directa para a pagina 1 da loja. Evita que o
        # standard tente resolver pricelists/publico e dispare o login.
        # Se um dia o cliente quiser landing custom, alterar aqui.
        return request.redirect('/shop/page/1')


class WebsiteArtigosController(http.Controller):
    """Catalogo simplificado `/artigos` paginado a partir de
    `product.template` publicados (`website_published=True`)."""

    @http.route(['/artigos', '/artigos/page/<int:page>'], type='http', auth='public', website=True, sitemap=True)
    def artigos_page(self, page=1, **kwargs):
        # sudo() intencional: o publico pode nao ter ACL sobre product.template
        # mesmo para registos publicados. Para o catalogo isto e aceitavel -
        # filtramos depois por website_published.
        Product = request.env['product.template'].sudo()
        products_per_page = 20
        offset = (page - 1) * products_per_page

        domain = [('website_published', '=', True)]
        total = Product.search_count(domain)
        products = Product.search(domain, limit=products_per_page, offset=offset)

        # Usar request.website.pager (e nao Website.pager) - o helper de
        # instancia em request.website ja resolve o contexto de website
        # ativo e e a forma recomendada nas versoes recentes do Odoo.
        pager = request.website.pager(
            url="/artigos",
            total=total,
            page=page,
            step=products_per_page,
            scope=5,
            url_args=kwargs,
        )

        # O template website.artigos NAO esta neste modulo. E criado via
        # Studio ou outro modulo do projeto - se faltar, falha aqui.
        return request.render('website.artigos', {
            'products': products,
            'pager': pager,
        })


class ShopRedirectController(http.Controller):
    """Rota `/smart-shop` que decide o destino conforme o utilizador."""

    @http.route(['/smart-shop'], type='http', auth='public', website=True, sitemap=False)
    def smart_shop_redirect(self, **kwargs):
        user = request.env.user
        # Publico -> catalogo simplificado; autenticado -> loja standard.
        # Util em links de campanha/QR onde nao sabemos a priori quem clica.
        if user and not user._is_public():
            return request.redirect('/shop')
        return request.redirect('/artigos')
