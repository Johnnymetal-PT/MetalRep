from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class MyWebsite(http.Controller):
    @http.route('/', type='http', auth='public', website=True)
    def custom_homepage(self):
        _logger.info('Custom homepage route called')

        website = request.env['website'].get_current_website()
        user = request.env.user
        partner = user.partner_id

        # Get allowed category names
        if website.is_website_product_visibility:
            if user._is_public():
                allowed_categories = website.visitor_product_categ_ids
            else:
                allowed_categories = partner.product_categ_ids
            allowed_names = set(allowed_categories.mapped('name'))
            _logger.info('Allowed category names: %s', list(allowed_names))
        else:
            allowed_names = set()

        # Find the "Todas" parent category
        todas_category = request.env['product.public.category'].search([('name', '=', 'Todas')], limit=1)
        visible_categories = []
        seen_ids = set()

        if todas_category:
            _logger.info("Todas category found: %s (ID: %d)", todas_category.name, todas_category.id)
            for category in todas_category.child_id:
                _logger.info("Inspecting child category: %s (ID: %d)", category.name, category.id)

                if category.name in allowed_names:
                    if category.id not in seen_ids:
                        _logger.info(" → Adding visible category: %s (ID: %d)", category.name, category.id)
                        visible_categories.append(category)
                        seen_ids.add(category.id)
                    else:
                        _logger.warning(" → Duplicate category skipped: %s (ID: %d)", category.name, category.id)
                else:
                    _logger.info(" → Category not allowed: %s (ID: %d)", category.name, category.id)

        # Final diagnostics
        _logger.info("Final visible categories sent to view:")
        for cat in visible_categories:
            _logger.info(" - %s (ID: %d) [%s]", cat.name, cat.id, hex(id(cat)))

        return request.render('pg_website.homepage_test', {
            'visible_categories': visible_categories
        })

