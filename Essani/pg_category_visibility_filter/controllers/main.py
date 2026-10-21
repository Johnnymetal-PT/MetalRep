"""Complemento ao filtro de produtos que remove categorias sem produtos visiveis."""
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo import http
from odoo.http import request


class WebsiteSaleCustom(WebsiteSale):
    def _get_pg_visible_public_category_ids(self, website):
        visible_products = request.env['product.template'].sudo().search(
            website.sale_product_domain()
        )
        visible_public_categories = visible_products.mapped('public_categ_ids')
        pg_visible_category_ids = set()

        # Keep parent categories visible when only child categories contain visible products.
        for category_record in visible_public_categories:
            current_category = category_record
            while current_category:
                if current_category.id in pg_visible_category_ids:
                    break
                pg_visible_category_ids.add(current_category.id)
                current_category = current_category.parent_id

        return pg_visible_category_ids

    @http.route()
    def shop(self, page=0, category=None, search='', min_price=0.0, max_price=0.0, tags='', **post):
        response = super().shop(
            page=page,
            category=category,
            search=search,
            min_price=min_price,
            max_price=max_price,
            tags=tags,
            **post
        )
        if not hasattr(response, 'qcontext'):
            return response

        website = request.website
        if not getattr(website, 'is_website_product_visibility', False):
            return response

        pg_visible_category_ids = self._get_pg_visible_public_category_ids(website)
        response.qcontext['pg_apply_category_filter'] = True
        response.qcontext['pg_visible_category_ids'] = list(pg_visible_category_ids)

        if 'categories' in response.qcontext:
            response.qcontext['categories'] = response.qcontext['categories'].filtered(
                lambda category_record: category_record.id in pg_visible_category_ids
            )

        return response
