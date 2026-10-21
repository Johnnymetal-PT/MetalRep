# -*- coding: utf-8 -*-
"""Tabela de aproveitamento de tecido (`pg_price_table`).

ATENCAO: o nome dos campos e `price_*` por razoes historicas, mas o
conteudo e a QUANTIDADE de tecido (em metros) por unidade produzida
quando se faz 1, 2, ... 10 unidades. NAO sao precos. Renomear
implicaria migracao - manter assim e documentar.

Ver `__manifest__.py` para o guia completo.
"""

from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Tabela de aproveitamento de tecido: 10 colunas (1..10 unidades).
    # Guardam METROS de tecido por unidade, nao precos (apesar do nome).
    price_1 = fields.Float(string="Price 1")
    price_2 = fields.Float(string="Price 2")
    price_3 = fields.Float(string="Price 3")
    price_4 = fields.Float(string="Price 4")
    price_5 = fields.Float(string="Price 5")
    price_6 = fields.Float(string="Price 6")
    price_7 = fields.Float(string="Price 7")
    price_8 = fields.Float(string="Price 8")
    price_9 = fields.Float(string="Price 9")
    price_10 = fields.Float(string="Price 10")

