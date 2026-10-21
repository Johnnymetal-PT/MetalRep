from odoo import models, fields, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    x_studio_cliente_1 = fields.Many2one('res.partner', string="Cliente", compute='_compute_so_fields', store=True)
    x_studio_referncia_do_cliente_2 = fields.Char(string="Ref Cliente", compute='_compute_so_fields', store=True)
    x_studio_sale_order_name = fields.Char(string="Encomenda", compute='_compute_so_fields', store=True)

    @api.depends('origin')
    def _compute_so_fields(self):
        for record in self:
            record.x_studio_cliente_1 = False
            record.x_studio_referncia_do_cliente_2 = False
            record.x_studio_sale_order_name = False

            if record.origin:
                # Step 1: Find the related PO from stock.picking origin
                po = self.env['purchase.order'].search([('name', '=', record.origin)], limit=1)

                if po and po.origin:
                    # Step 2: Find the related MO from PO origin
                    mo = self.env['mrp.production'].search([('name', '=', po.origin)], limit=1)

                    if mo and mo.origin:
                        # Step 3: Find the related SO from MO origin
                        so = self.env['sale.order'].search([('name', '=', mo.origin)], limit=1)

                        if so:
                            # Assign values from SO
                            record.x_studio_cliente_1 = so.partner_id.id
                            record.x_studio_referncia_do_cliente_2 = so.client_order_ref
                            record.x_studio_sale_order_name = so.name  # Fetch SO name
