# -*- coding: utf-8 -*-
"""Campos da "Tabela de Consumo" do produto, usada pelas Ordens de Fabrico.

NOTA IMPORTANTE: estes campos chamam-se `price_N` mas guardam QUANTIDADES a consumir
por escalão de quantidade produzida (1 a 10), não preços. Ver o __manifest__.py.
"""
from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Tabela de Consumo: um valor (quantidade a consumir) por escalão de produção.
    # price_1 = escalão até 1 unidade, price_2 = até 2, ..., price_10 = até 10.
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

