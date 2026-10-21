"""Controladores que protegem loja, produtos e pagina de categorias para visitantes anonimos."""
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.pg_web_attach_pdf_view.controllers.categories_page import PgCategoriesPage


def _pg_login_redirect():
    return request.redirect(f'/web/login?redirect={request.httprequest.path}')


def _pg_is_public_user():
    return request.env.user._is_public()


def _pg_resolve_category_id(category):
    if not category:
        return 0
    if isinstance(category, str):
        try:
            return int(category)
        except (TypeError, ValueError):
            return 0
    return category.id


class WebsiteSaleAuthRequired(WebsiteSale):

    @http.route()
    def shop(self, page=0, category=None, search='', min_price=0.0, max_price=0.0, tags='', **post):
        if _pg_is_public_user():
            cat_id = _pg_resolve_category_id(category)
            if cat_id:
                allowed_ids = request.website._pg_get_public_allowed_category_ids()
                if cat_id not in allowed_ids:
                    return _pg_login_redirect()
        return super().shop(
            page=page,
            category=category,
            search=search,
            min_price=min_price,
            max_price=max_price,
            tags=tags,
            **post,
        )

    @http.route()
    def product(self, product, category=None, pricelist=None, **kwargs):
        if _pg_is_public_user():
            return _pg_login_redirect()
        return super().product(product, category=category, pricelist=pricelist, **kwargs)


class PgCategoriesPageAuth(PgCategoriesPage):

    @http.route()
    def categories_page(self):
        if _pg_is_public_user():
            return _pg_login_redirect()
        return super().categories_page()
