from odoo import models, fields, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    so_id = fields.Many2one('sale.order', string='Source SO', compute='_compute_so_fields', store=True)
    mo_id = fields.Many2one('mrp.production', string='Source MO', compute='_compute_so_fields', store=True)
    so_name = fields.Char(string='SO Name', compute='_compute_so_fields', store=True)
    customer_ref = fields.Char(string='Customer Reference', compute='_compute_so_fields', store=True)
    mo_product_id = fields.Many2one('product.product', string='MO Product', compute='_compute_so_fields', store=True)

    @api.depends('origin')
    def _compute_so_fields(self):
        for picking in self:
            picking.so_id = False
            picking.mo_id = False
            picking.so_name = False
            picking.customer_ref = False
            picking.mo_product_id = False

            if picking.picking_type_code != 'incoming':
                continue

            # Find PO from picking origin
            po = self.env['purchase.order'].search([('name', '=', picking.origin)], limit=1)
            if po and po.origin:
                # Find MO from PO origin
                mo = self.env['mrp.production'].search([('name', '=', po.origin)], limit=1)
                if mo:
                    picking.mo_id = mo
                    picking.mo_product_id = mo.product_id
                    if mo.origin:
                        # Find SO from MO origin
                        so = self.env['sale.order'].search([('name', '=', mo.origin)], limit=1)
                        if so:
                            picking.so_id = so
                            picking.so_name = so.name
                            picking.customer_ref = so.x_studio_customer_ref

