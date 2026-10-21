from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo import http
from odoo.http import request


class WebsiteSaleCustom(WebsiteSale):
    def _get_search_domain(self, search, category, attrib_values):
        domain = super()._get_search_domain(search, category, attrib_values)
        partner = request.env.user.partner_id
        if partner:
            hidden = request.env['res.partner.product.visibility'].sudo().search([
                ('partner_id', '=', partner.id),
                ('visible', '=', False)
            ])
            product_ids = hidden.filtered('product_id').mapped('product_id').ids
            category_ids = hidden.filtered('category_id').mapped('category_id').ids
            if product_ids:
                domain += [('id', 'not in', product_ids)]
            if category_ids:
                domain += [('public_categ_ids', 'not in', category_ids)]
        return domain

    @http.route(['/shop', '/shop/page/<int:page>', '/shop/category/<model("product.public.category"):category>', 
                 '/shop/category/<model("product.public.category"):category>/page/<int:page>'], type='http', auth="public", website=True)
    def shop(self, page=0, category=None, search='', **post):
        response = super().shop(page=page, category=category, search=search, **post)
        partner = request.env.user.partner_id
        if not partner:
            return response

        hidden = request.env['res.partner.product.visibility'].sudo().search([
            ('partner_id', '=', partner.id),
            ('visible', '=', False)
        ])
        hidden_product_ids = hidden.filtered('product_id').mapped('product_id').ids
        hidden_category_ids = hidden.filtered('category_id').mapped('category_id').ids

        # Hide categories in sidebar
        if 'categories' in response.qcontext:
            def is_visible_category(cat):
                if cat.id in hidden_category_ids:
                    return False
                descendant_ids = cat.get_descendants().ids if hasattr(cat, 'get_descendants') else [cat.id]
                products = request.env['product.template'].search([
                    ('public_categ_ids', 'in', descendant_ids),
                    ('sale_ok', '=', True),
                    ('website_published', '=', True),
                    ('id', 'not in', hidden_product_ids)
                ], limit=1)
                return bool(products)

            response.qcontext['categories'] = response.qcontext['categories'].filtered(is_visible_category)

        # Hide breadcrumbs
        if 'breadcrumb' in response.qcontext:
            response.qcontext['breadcrumb'] = []

        return response
