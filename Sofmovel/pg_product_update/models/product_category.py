"""Imagens auxiliares em product.category (usadas pelo website).

Pertence ao modulo `pg_product_update`. Sao preenchidas automaticamente quando
o orquestrador cria uma categoria filha de "All" e encontra ate 2 imagens na
respetiva pasta.
"""
from odoo import models, fields

class ProductCategory(models.Model):
    """Adiciona `cat_image_1` e `cat_image_2` a `product.category`."""

    _inherit = 'product.category'

    # Campos binarios separados para expor imagens auxiliares no website.
    cat_image_1 = fields.Binary(string='Imagem 1', attachment=True)
    cat_image_2 = fields.Binary(string='Imagem 2', attachment=True)
