# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    # Nome do lote
    lot_name = fields.Char(
        string='Lote',
        default='SEM-LOTE',
        help='Lote a ser criado no recebimento'
    )

    def _prepare_stock_move_vals(self, picking, price_unit, product_uom_qty, product_uom):
        """Override para passar lot_name para o stock.move."""
        vals = super()._prepare_stock_move_vals(picking, price_unit, product_uom_qty, product_uom)
        if self.lot_name:
            vals['lot_name'] = self.lot_name
        return vals
