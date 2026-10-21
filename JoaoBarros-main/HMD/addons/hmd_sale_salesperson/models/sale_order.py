from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    salesperson_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Salesperson",
        help="Salesperson contact associated with the order.",
    )
