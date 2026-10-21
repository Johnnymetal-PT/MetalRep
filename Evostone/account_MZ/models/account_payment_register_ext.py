from odoo import models, fields


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    is_avenca = fields.Boolean(string='é Avenca')
