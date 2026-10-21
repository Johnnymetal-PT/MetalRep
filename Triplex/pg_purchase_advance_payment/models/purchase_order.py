# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # Adiantamentos (botão "Registar adiantamento") e pagamentos feitos pelas faturas da
    # encomenda (ligados pelo assistente de pagamento, ver wizard/).
    pg_advance_payment_ids = fields.One2many(
        'account.payment', 'pg_purchase_order_id', string="Vendor Payments")
    # compute_sudo: os utilizadores de Compras não têm ACL sobre account.payment, mas
    # devem ver o valor adiantado na encomenda.
    pg_advance_count = fields.Integer(
        string="Advance Count",
        compute='_compute_pg_advance', compute_sudo=True)
    pg_advance_amount = fields.Monetary(
        string="Paid to Vendor",
        compute='_compute_pg_advance', compute_sudo=True)
    pg_amount_after_advance = fields.Monetary(
        string="Remaining to Pay",
        compute='_compute_pg_advance', compute_sudo=True)

    @api.depends('amount_total', 'currency_id',
                 'pg_advance_payment_ids.state', 'pg_advance_payment_ids.amount',
                 'pg_advance_payment_ids.currency_id', 'pg_advance_payment_ids.date',
                 'pg_advance_payment_ids.payment_type')
    def _compute_pg_advance(self):
        for order in self:
            payments = order.pg_advance_payment_ids.filtered(lambda p: p.state != 'cancel')
            amount = 0.0
            # Só os lançados contam para o valor; os rascunhos aparecem no smart button.
            for payment in payments.filtered(lambda p: p.state == 'posted'):
                converted = payment.currency_id._convert(
                    payment.amount, order.currency_id, order.company_id,
                    payment.date or fields.Date.context_today(order))
                # Um reembolso do fornecedor (inbound) ligado à encomenda abate ao adiantado.
                amount += converted if payment.payment_type == 'outbound' else -converted
            order.pg_advance_count = len(payments)
            order.pg_advance_amount = amount
            order.pg_amount_after_advance = order.amount_total - amount

    def _pg_advance_payment_context(self):
        self.ensure_one()
        return {
            'default_payment_type': 'outbound',
            'default_partner_type': 'supplier',
            'default_partner_id': self.partner_id.commercial_partner_id.id,
            'default_currency_id': self.currency_id.id,
            'default_ref': self.name,
            'default_pg_purchase_order_id': self.id,
            # Mesmo contexto da ação standard "Pagamentos a fornecedores".
            'default_move_journal_types': ('bank', 'cash'),
            'display_account_trust': True,
        }

    def action_pg_register_advance(self):
        self.ensure_one()
        context = self._pg_advance_payment_context()
        context['default_amount'] = max(self.pg_amount_after_advance, 0.0)
        return {
            'type': 'ir.actions.act_window',
            'name': _("Advance Payment"),
            'res_model': 'account.payment',
            'view_mode': 'form',
            'target': 'current',
            'context': context,
        }

    def action_pg_view_advances(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Vendor Payments"),
            'res_model': 'account.payment',
            'view_mode': 'tree,form',
            'views': [(self.env.ref('account.view_account_supplier_payment_tree').id, 'tree'),
                      (False, 'form')],
            'domain': [('pg_purchase_order_id', '=', self.id)],
            'context': self._pg_advance_payment_context(),
        }
