# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    unreconciled_cash_count = fields.Integer(
        string='Movimentos Não Reconciliados',
        compute='_compute_unreconciled_cash_count',
    )

    @api.depends('type')
    def _compute_unreconciled_cash_count(self):
        """Conta os movimentos não reconciliados do diário de caixa."""
        for journal in self:
            if journal.type == 'cash':
                # Buscar contas outstanding do diário
                outstanding_accounts = (
                    journal.inbound_payment_method_line_ids.mapped('payment_account_id') |
                    journal.outbound_payment_method_line_ids.mapped('payment_account_id')
                )
                if outstanding_accounts:
                    count = self.env['account.move.line'].search_count([
                        ('journal_id', '=', journal.id),
                        ('parent_state', '=', 'posted'),
                        ('reconciled', '=', False),
                        ('account_id', 'in', outstanding_accounts.ids),
                    ])
                    journal.unreconciled_cash_count = count
                else:
                    journal.unreconciled_cash_count = 0
            else:
                journal.unreconciled_cash_count = 0

    def action_export_unreconciled_cash(self):
        """Abre o wizard para exportar movimentos de caixa (fecho)."""
        self.ensure_one()
        return {
            'name': _('Fecho de Caixa - Exportar'),
            'type': 'ir.actions.act_window',
            'res_model': 'cash.export.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_journal_id': self.id,
            },
        }

    def action_import_cash_statement(self):
        """Abre o wizard para confirmar pendentes (importar extracto)."""
        self.ensure_one()
        return {
            'name': _('Fecho de Caixa - Confirmar Pendentes'),
            'type': 'ir.actions.act_window',
            'res_model': 'cash.import.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_journal_id': self.id,
            },
        }

    def action_view_unreconciled_cash(self):
        """Mostra os movimentos não reconciliados do diário de caixa."""
        self.ensure_one()
        # Buscar contas outstanding do diário
        outstanding_accounts = (
            self.inbound_payment_method_line_ids.mapped('payment_account_id') |
            self.outbound_payment_method_line_ids.mapped('payment_account_id')
        )
        return {
            'name': _('Movimentos Não Reconciliados'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.line',
            'view_mode': 'list,form',
            'domain': [
                ('journal_id', '=', self.id),
                ('parent_state', '=', 'posted'),
                ('reconciled', '=', False),
                ('account_id', 'in', outstanding_accounts.ids),
            ],
            'context': {
                'search_default_group_by_move': 1,
            },
        }
