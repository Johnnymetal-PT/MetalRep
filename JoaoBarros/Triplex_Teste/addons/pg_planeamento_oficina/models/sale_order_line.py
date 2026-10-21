# -*- coding: utf-8 -*-
from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _create_planeamento_line(self):
        Planeamento = self.env['pg.planeamento.line'].sudo()
        existing = Planeamento.search([('sale_line_id', 'in', self.ids)])
        already = set(existing.mapped('sale_line_id').ids)
        to_create = [{'sale_line_id': line.id} for line in self if line.id not in already]
        if to_create:
            Planeamento.create(to_create)

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._create_planeamento_line()
        return lines
