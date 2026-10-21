# -*- coding: utf-8 -*-
"""Campos do wizard de agendamento para gravar limites por campanha."""
from odoo import fields, models


class MailingMailingScheduleDate(models.TransientModel):
    _inherit = "mailing.mailing.schedule.date"

    marketing_hourly_limit = fields.Integer(
        string="Hourly Send Limit",
        default=lambda self: self._default_limit("marketing_hourly_limit", 200),
        required=True,
        help="Maximum number of marketing emails to send each hour for this mailing.",
    )
    marketing_daily_limit = fields.Integer(
        string="Daily Send Limit",
        default=lambda self: self._default_limit("marketing_daily_limit", 5000),
        required=True,
        help="Maximum number of marketing emails to send per day for this mailing.",
    )

    def _default_limit(self, field_name, fallback):
        active_ids = self.env.context.get("active_ids") or []
        mailing = self.env["mailing.mailing"].browse(active_ids[:1]) if active_ids else False
        return mailing[field_name] if mailing and mailing[field_name] else fallback

    def action_schedule_date(self):
        res = super().action_schedule_date()
        active_ids = self.env.context.get("active_ids") or []
        if active_ids:
            self.env["mailing.mailing"].browse(active_ids).write(
                {
                    "marketing_hourly_limit": self.marketing_hourly_limit,
                    "marketing_daily_limit": self.marketing_daily_limit,
                }
            )
        return res
