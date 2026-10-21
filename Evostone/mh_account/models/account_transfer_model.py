from odoo import fields, models


class AccountTransferModel(models.Model):
    _inherit = "account.transfer.model"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)
