# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    manual_currency_rate_active = fields.Boolean(
        string='Aplicar Taxa de Câmbio Manual',
    )
    manual_currency_rate = fields.Float(
        string='Taxa de Câmbio Manual',
        digits=(12, 6),
    )
    manual_currency_rate_label = fields.Char(
        string='Conversão',
    )
