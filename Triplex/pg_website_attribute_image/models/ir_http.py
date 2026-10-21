# -*- encoding: utf-8 -*-
"""Otimização: remove os blobs de imagem da resposta do configurador de produto.

Em vez de enviar a imagem completa de cada valor de atributo no payload JSON do
configurador (pesado), substitui-a por um booleano (existe/não existe). A imagem em si
é depois carregada por URL quando necessário. Ver o __manifest__.py.
"""
import json
import logging

from odoo import models
from odoo.http import Response, request

_logger = logging.getLogger(__name__)
# Chaves de imagem a "achatar" para booleano no payload.
_IMAGE_KEYS = {
    "image",
    "image_128",
    "image_256",
    "image_512",
    "image_1024",
    "image_1920",
}


def _strip_images(payload):
    if isinstance(payload, dict):
        for key in _IMAGE_KEYS:
            if key in payload:
                payload[key] = bool(payload[key])
        for value in payload.values():
            _strip_images(value)
    elif isinstance(payload, list):
        for item in payload:
            _strip_images(item)


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _dispatch(cls, endpoint):
        response = super()._dispatch(endpoint)
        try:
            if (
                request
                and getattr(request, "httprequest", None)
                and request.httprequest.path == "/sale_product_configurator/get_values"
            ):
                if isinstance(response, Response):
                    raw = response.get_data(as_text=True)
                    data = json.loads(raw)
                    _strip_images(data)
                    new_raw = json.dumps(data)
                    response.set_data(new_raw)
                    _logger.info(
                        "pg_website_attribute_image_original: stripped images from configurator response"
                    )
                elif isinstance(response, dict):
                    _strip_images(response)
                    _logger.info(
                        "pg_website_attribute_image_original: stripped images from configurator response (dict)"
                    )
        except Exception:
            _logger.exception(
                "pg_website_attribute_image_original: failed to strip configurator images"
            )
        return response


