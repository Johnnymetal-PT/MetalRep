# -*- coding: utf-8 -*-
from odoo import models, api

CONSUMPTION_CLASSIFICATIONS = ('fixed_asset',)


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        for line in lines:
            if (
                line.picking_id
                and line.picking_id.picking_type_code == 'incoming'
                and line.product_id.product_classification in CONSUMPTION_CLASSIFICATIONS
            ):
                consumption_loc = self.env['stock.location'].search([
                    ('usage', '=', 'internal'),
                    ('is_consumption', '=', True),
                    ('company_id', '=', line.company_id.id),
                ], limit=1)
                if consumption_loc:
                    line.location_dest_id = consumption_loc
        return lines
