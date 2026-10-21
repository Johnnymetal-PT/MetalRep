"""Expoe no produto os campos de tabela de consumo usados na producao.

Os campos price_1..price_10 funcionam como uma grelha manual de consumo por
quantidade final a produzir.
"""

from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Tabela de consumo custom (1..10) usada pelo override de create() da MO.
    # Nota: semanticamente sao consumos, apesar do nome tecnico legacy `price_*`.
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

