from odoo import models, fields


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    posted_before = fields.Boolean(string='Posted Before', default=False)
