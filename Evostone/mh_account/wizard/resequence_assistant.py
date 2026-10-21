# -*- coding: utf-8 -*-
from datetime import date

from odoo import fields, models


_MONTHS = [
    ('1', 'Janeiro'), ('2', 'Fevereiro'), ('3', 'Março'), ('4', 'Abril'),
    ('5', 'Maio'), ('6', 'Junho'), ('7', 'Julho'), ('8', 'Agosto'),
    ('9', 'Setembro'), ('10', 'Outubro'), ('11', 'Novembro'), ('12', 'Dezembro'),
]


class ResequenceAssistant(models.TransientModel):
    _name = 'mh_account.resequence.assistant'
    _description = 'Assistente Resequenciar'

    journal_ids = fields.Many2many(
        'account.journal', string='Diários',
        domain=[('type', 'in', ['bank', 'cash', 'general', 'credit'])],
        required=True,
    )
    year = fields.Selection(
        [(str(y), str(y)) for y in range(date.today().year - 3, date.today().year + 2)],
        string='Ano', required=True, default=lambda s: str(date.today().year),
    )
    month_from = fields.Selection(_MONTHS, string='Mês De', required=True, default='1')
    month_to = fields.Selection(
        _MONTHS, string='Mês Até', required=True,
        default=lambda s: str(date.today().month),
    )
    dry_run = fields.Boolean(string='Dry-run (preview)', default=True)
    preview_text = fields.Text(string='Preview', readonly=True)
