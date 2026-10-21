"""
Campo de imagem em valores de atributo para configurador/fichas do website.

Modulo: pg_website_attribute_image.
Ficheiro: pg_website_attribute_image/models/product_attribute.py.
Modelos principais: product.attribute.value, product.template.attribute.value.

Além do campo `image`, este ficheiro expõe dois campos derivados que existem para
manter a amostra **fora** do HTML da ficha de produto:

- `has_image`: booleano guardado, para o template saber se há amostra sem ter de ler
  o ficheiro. Ler `image` obriga a carregar o anexo inteiro do filestore; num produto
  com 102 tecidos isso são ~23 MB lidos e codificados em base64 a cada visita.
- `image_url`: URL público da amostra já redimensionada, com chave de cache derivada
  da última escrita (mesmo mecanismo do `website.image_url`, ver
  `addons/website/models/website.py`).

O URL aponta ao `product.attribute.value` e não ao `product.template.attribute.value`
de propósito: o mesmo tecido tem o mesmo URL em todas as fichas do catálogo, por isso
uma única entrada na cache do browser serve o site inteiro. Por `product.template.
attribute.value` haveria um URL distinto por produto (110 938 registos contra 2 464) e
a cache deixava de ser reaproveitada.
"""

# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import hashlib

from odoo import api, fields, models

# Dimensão a que a amostra é servida na loja. O `/web/image` redimensiona e guarda
# em cache do lado do servidor; o ficheiro original fica intacto.
SAMPLE_IMAGE_SIZE = "128x128"


class ProductAttributeValue(models.Model):
    _inherit = "product.attribute.value"

    image = fields.Image(
        string="Image",
        help="You can upload an image that will be used as the color of the attribute value.",
        max_width=False,
        max_height=False,
    )

    has_image = fields.Boolean(
        string="Tem amostra",
        compute="_compute_has_image",
        store=True,
        help="Indica se o valor tem imagem carregada. Guardado para que os templates "
        "possam decidir se mostram a amostra sem ler o ficheiro.",
    )

    image_url = fields.Char(
        string="URL da amostra",
        compute="_compute_image_url",
        help="URL público da amostra redimensionada, com chave de cache derivada da "
        "última escrita no valor de atributo.",
    )

    @api.depends("image")
    def _compute_has_image(self):
        for value in self:
            value.has_image = bool(value.image)

    @api.depends("has_image", "write_date")
    def _compute_image_url(self):
        for value in self:
            # `_origin` devolve o registo real quando estamos num onchange sobre um
            # registo ainda por gravar (id virtual), que não serve para montar o URL.
            record_id = value._origin.id
            if not value.has_image or not record_id:
                value.image_url = False
                continue
            cache_key = hashlib.sha512(
                str(value.write_date).encode("utf-8")
            ).hexdigest()[:7]
            value.image_url = "/web/image/product.attribute.value/%s/image/%s?unique=%s" % (
                record_id,
                SAMPLE_IMAGE_SIZE,
                cache_key,
            )


class ProductTemplateAttributeValue(models.Model):
    _inherit = "product.template.attribute.value"

    # Campos relacionados (avaliados em sudo, como qualquer `related`) para que os
    # templates da loja não tenham de atravessar até ao `product.attribute.value`.
    # O nome `image_url` é o que o configurador do backend já procura em
    # `static/src/js/ptav_image_backend.js`.
    has_image = fields.Boolean(related="product_attribute_value_id.has_image")
    image_url = fields.Char(related="product_attribute_value_id.image_url")
