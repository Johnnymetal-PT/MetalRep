"""Replica dos campos cat_image_1/cat_image_2 (ver pg_categories_image).

NOTA: estes campos estao DUPLICADOS aqui e em pg_categories_image.
Os dois modulos definem o mesmo campo - quem instalar ambos vai
ter o mesmo campo declarado duas vezes (sem erro, mas confuso).
Decisao por validar: manter apenas em pg_categories_image e
remover daqui.
"""
from odoo import models, fields


class ProductCategory(models.Model):
    _inherit = 'product.category'

    cat_image_1 = fields.Binary(string='Imagem 1', attachment=True)
    cat_image_2 = fields.Binary(string='Imagem 2', attachment=True)
