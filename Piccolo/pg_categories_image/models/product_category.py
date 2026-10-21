"""Campos extra de imagem em ``product.category``.

Disponibiliza dois ``Binary(attachment=True)`` para serem consumidos
por templates QWeb do website (banners, hover, segundo plano).
"""
from odoo import models, fields


class ProductCategory(models.Model):
    _inherit = 'product.category'

    # attachment=True grava em ir.attachment (recomendado para imagens grandes;
    # evita inchar a tabela product_category).
    cat_image_1 = fields.Binary(string='Imagem 1', attachment=True)
    cat_image_2 = fields.Binary(string='Imagem 2', attachment=True)
