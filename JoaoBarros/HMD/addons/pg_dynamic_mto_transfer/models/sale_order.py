from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    internal_transfer_ids = fields.One2many(
        'stock.picking',
        compute='_compute_internal_transfer_ids',
        store=False
    )

    @api.depends('picking_ids.picking_type_id.code')
    def _compute_internal_transfer_ids(self):
        for order in self:
            order.internal_transfer_ids = order.picking_ids.filtered(
                lambda p: p.picking_type_id.code == 'internal'
            )

    def action_view_internal_transfers(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Internal Transfers',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'domain': [('id', 'in', self.internal_transfer_ids.ids)],
            'context': {'create': False},
        }


#class SaleOrderLine(models.Model):
#    _inherit = 'sale.order.line'
#
#    product_variant_desc = fields.Char(
#        string="Variant Description (Dummy)",
#        compute="_compute_dummy_variant_desc",
#        store=False
#    )
#
#    def _compute_dummy_variant_desc(self):
#        for line in self:
#            line.product_variant_desc = ""  # You can optionally put real logic here

