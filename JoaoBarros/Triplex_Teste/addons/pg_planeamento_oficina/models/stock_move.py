# -*- coding: utf-8 -*-
from odoo import api, fields, models

from .res_partner import SUPPLIER_TYPES


class StockMove(models.Model):
    _inherit = 'stock.move'

    x_supplier_type = fields.Selection(
        SUPPLIER_TYPES,
        string='Tipo de Fornecedor',
        compute='_compute_x_supplier_type',
        store=True,
    )
    x_vendor_id = fields.Many2one(
        'res.partner',
        string='Fornecedor',
        compute='_compute_x_supplier_type',
        store=True,
    )

    @api.depends('product_id', 'product_id.seller_ids',
                 'product_id.seller_ids.partner_id.x_supplier_type',
                 'product_id.seller_ids.sequence')
    def _compute_x_supplier_type(self):
        for move in self:
            sellers = move.product_id.seller_ids.sorted('sequence')
            typed = sellers.filtered(lambda s: s.partner_id.x_supplier_type)
            if typed:
                move.x_supplier_type = typed[0].partner_id.x_supplier_type
                move.x_vendor_id = typed[0].partner_id
            else:
                move.x_supplier_type = False
                move.x_vendor_id = False
