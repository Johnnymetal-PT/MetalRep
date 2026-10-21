# Copyright 2025 MH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    reason = fields.Char(
        string='Reason displayed on Credit Note',
        required=True,
    )

    def _prepare_default_reversal(self, move):
        """Override para copiar reason para credit_note_reason na NC"""
        vals = super()._prepare_default_reversal(move)
        vals['credit_note_reason'] = self.reason
        return vals
