# -*- coding: utf-8 -*-
from odoo import models, api


class AccountMoveSend(models.AbstractModel):
    _inherit = 'account.move.send'

    @api.model
    def _get_default_pdf_report_id(self, move):
        """Selecciona o report PDF consoante o tipo de documento."""
        report = False

        if move.move_type == 'out_invoice':
            report = self.env.ref(
                'mh_stone_reports.action_report_invoice_stone',
                raise_if_not_found=False,
            )
        elif move.move_type == 'out_refund':
            report = self.env.ref(
                'mh_stone_reports.action_report_credit_note_stone',
                raise_if_not_found=False,
            )
        elif move.move_type in ('in_refund', 'in_invoice'):
            report = self.env.ref(
                'mh_stone_reports.action_report_debit_note_stone',
                raise_if_not_found=False,
            )

        if report:
            return report

        return super()._get_default_pdf_report_id(move)
