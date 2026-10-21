from odoo import fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    x_studio_community = fields.Boolean(
        string="Community",
        default=False,
        copy=False,
    )
    x_studio_observaes_no_recibo = fields.Char(
        string="Observacoes No Recibo",
    )
