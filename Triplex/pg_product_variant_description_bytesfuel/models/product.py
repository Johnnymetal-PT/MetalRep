# -*- coding: utf-8 -*-
"""
Sincroniza descricao de variantes para linhas de venda e compra.

Modulo: pg_product_variant_description_bytesfuel.
Ficheiro: pg_product_variant_description_bytesfuel\models\product.py.
Modelos principais: product.product, sale.order.line e purchase.order.line.
"""

# Módulo de terceiros (Bytesfuel). Descrição por variante mostrada na loja e disponível
# em vendas/compras. Ver o __manifest__.py.
from odoo.http import request
from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)

class ProductProduct(models.Model):
    _inherit = 'product.product'

    # Descrição específica desta variante (traduzível). O campo "real" vive na variante;
    # nas linhas de venda/compra abaixo é apenas relacionado (só leitura).
    product_variant_desc = fields.Text(string='Variant Description', translate=True)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # Related field will inherit the translation capabilities
    product_variant_desc = fields.Text(related='product_id.product_variant_desc', string="Variant Description", readonly=True)

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    # Related field will inherit the translation capabilities
    product_variant_desc = fields.Text(
        related='product_id.product_variant_desc', 
        string="Variant Description", 
        readonly=True
    )

