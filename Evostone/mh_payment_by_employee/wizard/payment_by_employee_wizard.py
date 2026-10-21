# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from markupsafe import Markup
import logging

_logger = logging.getLogger(__name__)


class PaymentByEmployeeWizard(models.TransientModel):
    _name = 'payment.by.employee.wizard'
    _description = 'Pagamento por Funcionário'

    invoice_id = fields.Many2one(
        'account.move', string='Factura', required=True, readonly=True,
    )
    employee_id = fields.Many2one(
        'res.partner', string='Funcionário', required=True,
        help='Funcionário que pagou a factura.',
    )
    amount = fields.Monetary(
        string='Montante', required=True,
        currency_field='currency_id',
    )
    currency_id = fields.Many2one(
        related='invoice_id.currency_id',
    )
    invoice_residual = fields.Monetary(
        related='invoice_id.amount_residual',
        string='Saldo em Aberto',
    )
    date = fields.Date(
        string='Data',
        required=True,
        default=fields.Date.context_today,
        help='Data do lançamento PGF e da taxa de câmbio usada na conversão '
             'para a moeda da empresa (se a factura for em moeda estrangeira).',
    )

    @api.onchange('invoice_id')
    def _onchange_invoice_id(self):
        if self.invoice_id:
            self.amount = self.invoice_id.amount_residual

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'invoice_id' in res and 'amount' in fields_list:
            invoice = self.env['account.move'].browse(res['invoice_id'])
            res['amount'] = invoice.amount_residual
        return res

    def action_confirm(self):
        self.ensure_one()
        invoice = self.invoice_id
        employee = self.employee_id
        amount = self.amount

        # Validações
        if amount <= 0:
            raise UserError(_("O montante deve ser superior a zero."))
        if amount > invoice.amount_residual:
            raise UserError(_(
                "O montante (%(amount)s) não pode ser superior ao saldo em aberto (%(residual)s).",
                amount=amount,
                residual=invoice.amount_residual,
            ))

        # Buscar diário PGF
        pgf_journal = self.env['account.journal'].search(
            [('code', '=', 'PGF'), ('company_id', '=', invoice.company_id.id)],
            limit=1,
        )
        if not pgf_journal:
            raise UserError(_(
                "Diário PGF (Pagamentos por Funcionários) não encontrado.\n"
                "Crie um diário com código 'PGF' do tipo 'Operações Diversas'."
            ))

        # Buscar conta a pagar do fornecedor (a partir da linha da factura)
        supplier_payable_line = invoice.line_ids.filtered(
            lambda l: l.account_type == 'liability_payable'
                and l.partner_id == invoice.partner_id
        )
        if not supplier_payable_line:
            raise UserError(_(
                "Não foi possível encontrar a linha de conta a pagar do fornecedor na factura."
            ))
        supplier_payable = supplier_payable_line[0].account_id

        # Buscar conta a pagar do funcionário
        employee_payable = employee.property_account_payable_id
        if not employee_payable:
            raise UserError(_(
                "O funcionário '%s' não tem conta a pagar configurada.",
                employee.name,
            ))

        # Converter o montante (na moeda da factura) para a moeda da empresa,
        # à taxa da data escolhida. Em factura na moeda da empresa, o _convert
        # devolve o mesmo valor (sem alteração de comportamento).
        company = invoice.company_id
        company_currency = company.currency_id
        invoice_currency = invoice.currency_id
        amount_company = invoice_currency._convert(
            amount, company_currency, company, self.date,
        )

        # Linha do fornecedor: carrega a moeda da factura (amount_currency) para
        # casar na reconciliação; a diferença de câmbio (se a taxa da data ≠ taxa
        # da factura) é tratada automaticamente pelo Odoo ao reconciliar.
        supplier_line = {
            'name': 'Fecho dívida fornecedor (%s)' % invoice.name,
            'account_id': supplier_payable.id,
            'partner_id': invoice.partner_id.id,
            'debit': amount_company,
            'credit': 0,
            'currency_id': invoice_currency.id,
            'amount_currency': amount,
        }
        # Linha do funcionário: fica na moeda da empresa (dívida fixa à data).
        employee_line = {
            'name': '%s pagou por conta (%s)' % (employee.name, invoice.name),
            'account_id': employee_payable.id,
            'partner_id': employee.id,
            'debit': 0,
            'credit': amount_company,
            'currency_id': company_currency.id,
            'amount_currency': -amount_company,
        }

        # Criar lançamento PGF
        pgf_move = self.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': pgf_journal.id,
            'date': self.date,
            'ref': '%s - %s pagou factura %s' % (
                invoice.name, employee.name, invoice.partner_id.name,
            ),
            'pgf_source_invoice_id': invoice.id,
            'line_ids': [
                (0, 0, supplier_line),
                (0, 0, employee_line),
            ],
        })

        # Publicar
        pgf_move.action_post()

        # Reconciliar linha do fornecedor com a factura
        lines_to_reconcile = self.env['account.move.line'].search([
            ('partner_id', '=', invoice.partner_id.id),
            ('account_id', '=', supplier_payable.id),
            ('reconciled', '=', False),
            ('parent_state', '=', 'posted'),
            ('move_id', 'in', [invoice.id, pgf_move.id]),
        ])
        if lines_to_reconcile:
            lines_to_reconcile.reconcile()

        # Mensagem no chatter
        invoice.message_post(
            body=Markup(
                "Factura paga por <b>%s</b> no valor de <b>%s %s</b>. "
                "Lançamento PGF: <a href='#' data-oe-model='account.move' data-oe-id='%s'>%s</a>"
            ) % (
                employee.name,
                '{:,.2f}'.format(amount),
                invoice.currency_id.name,
                pgf_move.id,
                pgf_move.name,
            ),
        )

        _logger.info(
            "PGF: Factura %s paga por %s, montante=%.2f %s, lançamento=%s",
            invoice.name, employee.name, amount,
            invoice.currency_id.name, pgf_move.name,
        )

        return {'type': 'ir.actions.act_window_close'}
