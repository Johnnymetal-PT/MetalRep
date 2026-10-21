# -*- coding: utf-8 -*-
"""Campos persistentes de quota configurados em cada campanha de Email Marketing."""
from odoo import fields, models


class MailingMailing(models.Model):
    _inherit = "mailing.mailing"

    marketing_hourly_limit = fields.Integer(
        string="Hourly Send Limit",
        default=200,
        required=True,
        help="Maximum number of marketing emails to send each hour for this mailing.",
    )
    marketing_daily_limit = fields.Integer(
        string="Daily Send Limit",
        default=5000,
        required=True,
        help="Maximum number of marketing emails to send per day for this mailing.",
    )

    def action_schedule_date(self):
        action = getattr(super(), "action_schedule_date", None)
        if callable(action):
            return action()
        return True
