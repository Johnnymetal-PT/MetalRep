from odoo import models, fields, api
from datetime import datetime, timedelta

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_commitment_overdue = fields.Boolean(
        string="Overdue Commitment",
        compute='_compute_commitment_alerts',
        store=False
    )
    is_commitment_soon = fields.Boolean(
        string="Upcoming Commitment",
        compute='_compute_commitment_alerts',
        store=False
    )

    custom_tag_ids = fields.Many2many('sale.order.tag', string="Custom Tags")
    
    @api.depends('commitment_date')
    def _compute_commitment_alerts(self):
        today = datetime.today().date()
        soon_threshold = today + timedelta(weeks=3)
        for order in self:
            order.is_commitment_overdue = False
            order.is_commitment_soon = False
            if order.commitment_date:
                commitment = order.commitment_date.date() if isinstance(order.commitment_date, datetime) else order.commitment_date
                order.is_commitment_overdue = commitment < today
                order.is_commitment_soon = today <= commitment <= soon_threshold

class SaleOrderTag(models.Model):
    _name = 'sale.order.tag'
    _description = 'Sales Order Tag'

    name = fields.Char(required=True)
    color = fields.Integer(string="Color Index")
