# -*- coding: utf-8 -*-
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    cogs_price_diff_journal_id = fields.Many2one(
        'account.journal',
        string='Diário Ajuste CMV Diferença de Preço',
        help='Diário usado para o lançamento que encaminha a diferença de preço '
             'da parte vendida das facturas de fornecedor para o CMV. '
             'Se não definido, usa-se o primeiro diário do tipo "general".',
    )
