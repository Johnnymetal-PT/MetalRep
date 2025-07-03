from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class MyWebsite(http.Controller):
    @http.route('/HomePage', type='http', auth='public', website=True)
    def custom_homepage(self):
        _logger.info('Custom homepage route called')

        todas_category = request.env['product.public.category'].search([('name', '=', 'Todas')], limit=1)

        if todas_category:
            _logger.info('Todas category found: %s', todas_category.name)
            child_categories = todas_category.child_id
            if child_categories:
                _logger.info('Child categories found: %d', len(child_categories))
                for category in child_categories:
                    _logger.info('Child Category: %s (ID: %d)', category.name, category.id)
            else:
                _logger.warning('No child categories found for Todas category')
        else:
            _logger.warning('Todas category not found')
            child_categories = []

        return request.render('pg_website.homepage_test', {'child_categories': child_categories})

    @http.route('/dynamic_menu', type='http', auth="public", website=True)
    def dynamic_menu(self):
        _logger.info('dynamic_menu route called')
        return request.render('pg_website.dynamic_menu_template', {})
