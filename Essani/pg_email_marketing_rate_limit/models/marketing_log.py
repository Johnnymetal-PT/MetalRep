# -*- coding: utf-8 -*-
"""Modelo de auditoria usado para calcular quotas de envio de Email Marketing."""
from odoo import fields, models


class EmailMarketingSendLog(models.Model):
    _name = "pg.email.marketing.log"
    _description = "Email Marketing Send Log"
    _order = "sent_at desc"

    mail_id = fields.Many2one(
        "mail.mail",
        string="Mail",
        required=True,
        ondelete="cascade",
        index=True,
    )
    mailing_id = fields.Many2one(
        "mailing.mailing",
        string="Mailing",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sent_at = fields.Datetime(
        string="Sent At",
        required=True,
        default=fields.Datetime.now,
        index=True,
    )
