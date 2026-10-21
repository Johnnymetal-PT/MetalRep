# -*- coding: utf-8 -*-

from odoo import models
import logging

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    """
    Extensão do product.product para mh_purchase.

    NOTA: A lógica PCMP é controlada pelo mh_stock_valuation.
    O campo pcmp está definido no mh_inventory.
    Este módulo não adiciona campos nem lógica PCMP ao produto.
    """
    _inherit = 'product.product'

    # Sem campos adicionais - mh_inventory define pcmp, mh_stock_valuation controla a lógica
    # O campo pcmp é definido em mh_inventory/models/product_product.py
