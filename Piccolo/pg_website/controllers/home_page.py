"""Controllers das paginas custom do website da Piccolo.

- ``/HomePage`` mostra a homepage custom com os filhos da categoria
  publica chamada "Todas".
- ``/dynamic_menu`` renderiza o template de menu dinamico.

A categoria "Todas" e procurada por nome literal - se nao existir, a
homepage carrega sem child categories (apenas com warning no log).
"""
from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class MyWebsite(http.Controller):

    @http.route('/HomePage', type='http', auth='public', website=True)
    def custom_homepage(self):
        _logger.info('Custom homepage route called')

        # Categoria de topo "Todas" e o ancora da homepage - se for
        # renomeada/eliminada, a homepage perde o conteudo dinamico.
        todas_category = request.env['product.public.category'].search(
            [('name', '=', 'Todas')], limit=1,
        )

        if todas_category:
            child_categories = todas_category.child_id
            if child_categories:
                _logger.info('Child categories found: %d', len(child_categories))
            else:
                _logger.warning('No child categories found for Todas category')
        else:
            _logger.warning('Todas category not found')
            child_categories = []

        return request.render(
            'pg_website.homepage_test',
            {'child_categories': child_categories},
        )

    @http.route('/dynamic_menu', type='http', auth="public", website=True)
    def dynamic_menu(self):
        # Template ``pg_website.dynamic_menu_template`` definido em
        # views/templates.xml.
        return request.render('pg_website.dynamic_menu_template', {})
