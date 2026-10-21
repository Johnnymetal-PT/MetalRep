"""Controller da pagina /categorias e redirect local de /shop para a entrada por familias."""
from odoo import http
from odoo.http import request


class PgCategoriesPage(http.Controller):
    @http.route(['/shop'], type='http', auth='public', website=True)
    def shop_redirect(self, **kwargs):
        return request.redirect('/categorias', code=301)

    @http.route(['/categories', '/categorias'], type='http', auth='public', website=True)
    def categories_page(self):
        website = request.env['website'].get_current_website()
        user = request.env.user
        partner = user.partner_id

        # Get allowed category names
        if getattr(website, "is_website_product_visibility", False):
            if user._is_public():
                allowed_categories = website.visitor_product_categ_ids
            else:
                allowed_categories = partner.product_categ_ids
            allowed_names = set(allowed_categories.mapped('name'))
        else:
            allowed_names = set()

        # Find the "Todas" parent category
        todas_category = request.env['product.public.category'].search([('name', '=', 'Todas')], limit=1)
        visible_categories = []
        seen_ids = set()

        if todas_category:
            for category in todas_category.child_id:
                if allowed_names and category.name not in allowed_names:
                    continue
                if category.id in seen_ids:
                    continue
                visible_categories.append(category)
                seen_ids.add(category.id)

        return request.render('pg_web_attach_pdf_view.categories_page', {
            'visible_categories': visible_categories,
        })
