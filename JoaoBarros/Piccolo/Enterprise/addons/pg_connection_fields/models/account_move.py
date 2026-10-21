from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    x_studio_community = fields.Boolean(
        string="Community",
        default=False,
        copy=False,
    )
