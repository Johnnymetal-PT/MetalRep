# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    cogs_price_diff_journal_id = fields.Many2one(
        'account.journal',
        related='company_id.cogs_price_diff_journal_id',
        readonly=False,
        string='Diário Ajuste CMV Diferença de Preço',
        help='Diário usado para encaminhar a diferença de preço da parte vendida '
             'das facturas de fornecedor para o CMV.',
    )
