"""Tabela de consumo dinamico (1..10 unidades) no product.template.

NOMES MISLEADING: ``price_*`` na realidade representam CONSUMOS por
quantidade total produzida, nao precos. Mantido por compatibilidade
com o pg_tecidos.
"""
from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # 10 slots fixos. Index N representa o consumo TOTAL esperado
    # quando a MO tem ``product_qty = N``. Para qty > 10 usa-se
    # price_10 (ver _get_consumption_value).
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
