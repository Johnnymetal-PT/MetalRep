from odoo import http
from odoo.http import request
from odoo.addons.website.controllers.main import Website

class ShopPublicAccess(http.Controller):
    @http.route('/shop', auth='public', website=True)
    def public_shop(self, **kwargs):
        return request.redirect('/shop/page/1')  # Or re-dispatch to the original controller

class WebsiteArtigosController(http.Controller):

    @http.route(['/artigos', '/artigos/page/<int:page>'], type='http', auth='public', website=True, sitemap=True)
    def artigos_page(self, page=1, **kwargs):
        Product = request.env['product.template'].sudo()
        products_per_page = 20
        offset = (page - 1) * products_per_page

        domain = [('website_published', '=', True)]
        total = Product.search_count(domain)
        products = Product.search(domain, limit=products_per_page, offset=offset)

        # ✅ Use request.website.pager — not Website.pager
        pager = request.website.pager(
            url="/artigos",
            total=total,
            page=page,
            step=products_per_page,
            scope=5,
            url_args=kwargs
        )

        return request.render('website.artigos', {
            'products': products,
            'pager': pager,
        })
        
class ShopRedirectController(http.Controller):

    @http.route(['/smart-shop'], type='http', auth='public', website=True, sitemap=False)
    def smart_shop_redirect(self, **kwargs):
        user = request.env.user
        if user and not user._is_public():
            return request.redirect('/shop')
        return request.redirect('/artigos')
