"""Imagem por valor de atributo para uso no website/configurador de produto.

Modulo: pg_website_attribute_image.
Ficheiro: pg_website_attribute_image/models/product_attribute.py.
Modelo principal: product.attribute.value.
"""
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductAttributeValue(models.Model):
    _inherit = "product.attribute.value"

    image = fields.Image(
        string="Image",
        # Mantem dimensao original para o frontend escolher o melhor redimensionamento.
        help="You can upload an image that will be used as the color of the attribute value.",
        max_width=False,
        max_height=False,
    )
