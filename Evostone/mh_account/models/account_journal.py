# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    receipt_prefix = fields.Char(
        string='Prefixo Recibo',
        help='Prefixo para numeração de recibos.',
    )

    mh_show_in_dashboard = fields.Boolean(
        string='Mostrar no Painel (utilizador actual)',
        compute='_compute_mh_show_in_dashboard',
        help='Indica se o diário deve aparecer no painel de contabilidade.',
    )

    def _compute_mh_show_in_dashboard(self):
        show_general_journals = self.env.user.has_group('base.group_system')
        for journal in self:
            journal.mh_show_in_dashboard = (
                journal.type != 'general' or show_general_journals
            )
