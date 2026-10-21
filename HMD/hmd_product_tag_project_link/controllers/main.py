import json

from odoo import http
from odoo.http import request


class HmdProductTagProjectLinkController(http.Controller):
    @http.route(
        '/hmd/product_tag_project_urls/<int:product_tmpl_id>',
        type='http',
        auth='public',
        website=True,
        csrf=False,
    )
    def product_tag_project_urls(self, product_tmpl_id, **kwargs):
        product = request.env['product.template'].sudo().browse(product_tmpl_id).exists()
        result = {'tag_urls': {}}
        if product:
            tags = product.product_tag_ids
            if 'all_product_tag_ids' in product._fields:
                tags |= product.all_product_tag_ids

            for tag in tags:
                if not tag.visible_on_ecommerce or not tag.hmd_project_page_url:
                    continue
                raw_url = (tag.hmd_project_page_url or '').strip()
                if not raw_url:
                    continue
                if raw_url.startswith(('http://', 'https://', '/')):
                    normalized_url = raw_url
                else:
                    normalized_url = '/' + raw_url
                result['tag_urls'][tag.name] = normalized_url

        headers = [('Content-Type', 'application/json')]
        return request.make_response(json.dumps(result), headers=headers)
