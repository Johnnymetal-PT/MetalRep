# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    receipt_number = fields.Char(
        string='Nº Recibo',
        copy=False,
        readonly=True,
        index=True,
        help='Número do recibo.',
    )

    _sql_constraints = [
        ('receipt_number_unique', 'UNIQUE(receipt_number)',
         'O número de recibo deve ser único.'),
    ]

    manual_currency_rate_active = fields.Boolean(
        string='Aplicar Taxa de Câmbio Manual',
        copy=False,
        tracking=True,
    )

    manual_currency_rate = fields.Float(
        string='Taxa de Câmbio Manual',
        digits=(12, 6),
        copy=False,
        tracking=True,
    )

    manual_currency_rate_label = fields.Char(
        string='Conversão',
    )
