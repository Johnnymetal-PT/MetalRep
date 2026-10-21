# -*- coding: utf-8 -*-

import json
import logging

from odoo import http
from odoo.addons.sale_product_configurator.controllers.main import ProductConfiguratorController

_logger = logging.getLogger(__name__)


def _strip_ptav_images(payload):
    """Remove heavy image payload from configurator JSON response."""
    stripped = 0

    def _walk(node):
        nonlocal stripped
        if isinstance(node, dict):
            if "image" in node:
                image_value = node.pop("image", None)
                if image_value:
                    stripped += 1
            for value in node.values():
                _walk(value)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(payload)
    return stripped


class ProductConfiguratorControllerNoInlineImage(ProductConfiguratorController):
    @http.route('/sale_product_configurator/get_values', type='json', auth='user', methods=['POST'])
    def get_values(self, *args, **kwargs):
        response = super().get_values(*args, **kwargs)
        removed_count = _strip_ptav_images(response)

        if removed_count:
            try:
                response_size = len(json.dumps(response, default=str))
            except Exception:  # pragma: no cover
                response_size = -1
            _logger.info(
                "pg_website_attribute_image stripped %s inline ptav images from /sale_product_configurator/get_values payload (size=%s bytes)",
                removed_count,
                response_size,
            )

        return response
