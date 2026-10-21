# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    transfer_account_id = fields.Many2one(
        'account.account',
        string='Conta de Transferência Interna (12404)',
        help='Conta intermédia usada para transferências entre diários (ex: 12404 Transferência Interna)',
        domain="[('company_ids', 'in', company_id), ('account_type', 'in', ['asset_current', 'liability_current'])]",
    )
    outstanding_receipts_account_id = fields.Many2one(
        'account.account',
        string='Conta de Recebimentos Pendentes (12402)',
        help='Conta usada para recebimentos pendentes no destino (ex: 12402 Recebimentos Pendentes)',
        domain="[('company_ids', 'in', company_id), ('account_type', 'in', ['asset_current', 'liability_current']), ('reconcile', '=', True)]",
    )
    outstanding_payments_account_id = fields.Many2one(
        'account.account',
        string='Conta de Pagamentos Pendentes (12403)',
        help='Conta usada para pagamentos pendentes na origem (ex: 12403 Pagamentos Pendentes)',
        domain="[('company_ids', 'in', company_id), ('account_type', 'in', ['asset_current', 'liability_current']), ('reconcile', '=', True)]",
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        config_param = self.env['ir.config_parameter'].sudo()

        transfer_account_id = config_param.get_param('internal_transfer.transfer_account_id')
        res['transfer_account_id'] = int(transfer_account_id) if transfer_account_id else False

        outstanding_receipts_account_id = config_param.get_param('internal_transfer.outstanding_receipts_account_id')
        res['outstanding_receipts_account_id'] = int(outstanding_receipts_account_id) if outstanding_receipts_account_id else False

        outstanding_payments_account_id = config_param.get_param('internal_transfer.outstanding_payments_account_id')
        res['outstanding_payments_account_id'] = int(outstanding_payments_account_id) if outstanding_payments_account_id else False

        return res

    def set_values(self):
        super().set_values()
        config_param = self.env['ir.config_parameter'].sudo()
        config_param.set_param(
            'internal_transfer.transfer_account_id',
            self.transfer_account_id.id if self.transfer_account_id else False
        )
        config_param.set_param(
            'internal_transfer.outstanding_receipts_account_id',
            self.outstanding_receipts_account_id.id if self.outstanding_receipts_account_id else False
        )
        config_param.set_param(
            'internal_transfer.outstanding_payments_account_id',
            self.outstanding_payments_account_id.id if self.outstanding_payments_account_id else False
        )
