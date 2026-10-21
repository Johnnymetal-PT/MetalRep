# -*- coding: utf-8 -*-

from odoo import models, api


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    @api.model
    def _set_initial_stock_location(self):
        """
        Configura a localização de origem do tipo de operação Stock Inicial.

        A localização "Inventory adjustment" é criada dinamicamente por empresa,
        por isso não pode ser referenciada via XML ID estático.
        """
        picking_type = self.env.ref(
            'mh_stock_valuation.picking_type_initial_stock',
            raise_if_not_found=False
        )
        if not picking_type:
            return

        # Procurar a localização de ajuste de inventário
        inventory_location = self.env['stock.location'].search([
            ('usage', '=', 'inventory'),
            '|',
            ('company_id', '=', picking_type.company_id.id),
            ('company_id', '=', False),
        ], limit=1)

        if inventory_location:
            picking_type.default_location_src_id = inventory_location.id
