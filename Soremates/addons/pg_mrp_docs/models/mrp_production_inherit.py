from odoo import fields, models, api

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Cliente',
        compute='_compute_partner_id',
        store=True,
    )
    date_order = fields.Date(
        string='Data',
        compute='_compute_date_order',
        store=True,
    )

    @api.depends('origin')
    def _compute_partner_id(self):
        for record in self:
            if record.origin:
                sale_order = self.env['sale.order'].search([('name', '=', record.origin)], limit=1)
                record.partner_id = sale_order.partner_id.id if sale_order else False

    @api.depends('origin')
    def _compute_date_order(self):
        for record in self:
            if record.origin:
                sale_order = self.env['sale.order'].search([('name', '=', record.origin)], limit=1)
                record.date_order = sale_order.date_order.date() if sale_order and sale_order.date_order else False


class StockMove(models.Model):
    _inherit = 'stock.move'

    x_studio_ral = fields.Selection(
        related='product_id.product_tmpl_id.x_studio_ral',
        string='RAL',
        store=True,
    )
    x_studio_espessura = fields.Float(
        related='product_id.product_tmpl_id.x_studio_espessura',
        string='Espessura',
        store=True,
    )

