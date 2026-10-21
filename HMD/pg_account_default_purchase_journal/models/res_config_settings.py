# -*- coding: utf-8 -*-
"""Exposição do diário por defeito de fornecedor nas Definições de Contabilidade."""

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pg_default_purchase_journal_id = fields.Many2one(
        related="company_id.pg_default_purchase_journal_id",
        string="Diário por defeito de faturas de fornecedor",
        readonly=False,
    )
