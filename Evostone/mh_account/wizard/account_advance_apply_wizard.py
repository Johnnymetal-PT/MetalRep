# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountAdvanceApplyWizard(models.TransientModel):
    _name = 'account.advance.apply.wizard'
    _description = 'Aplicação de Adiantamentos'

    invoice_id = fields.Many2one('account.move', string='Fatura', required=True)
    partner_id = fields.Many2one(
        'res.partner', string='Cliente/Fornecedor', related='invoice_id.partner_id',
        readonly=True,
    )
    currency_id = fields.Many2one(
        'res.currency', string='Moeda', related='invoice_id.currency_id', readonly=True,
    )
    invoice_residual = fields.Monetary(
        string='Valor Residual', related='invoice_id.amount_residual', readonly=True,
        currency_field='currency_id',
    )
    company_id = fields.Many2one(
        'res.company', string='Empresa', related='invoice_id.company_id', readonly=True,
    )
    advance_line_ids = fields.One2many(
        'account.advance.apply.wizard.line', 'wizard_id', string='Adiantamentos',
    )
    total_advances_selected = fields.Monetary(
        string='Total Selecionado', currency_field='currency_id',
    )
    total_to_apply = fields.Monetary(
        string='Total a Aplicar', currency_field='currency_id',
    )


class AccountAdvanceApplyWizardLine(models.TransientModel):
    _name = 'account.advance.apply.wizard.line'
    _description = 'Linha de Aplicação de Adiantamentos'

    wizard_id = fields.Many2one(
        'account.advance.apply.wizard', string='Wizard', required=True,
        ondelete='cascade',
    )
    advance_payment_id = fields.Many2one(
        'account.payment', string='Adiantamento', required=True,
        domain=[('is_advance', '=', True)],
    )
    advance_date = fields.Date(
        string='Data', related='advance_payment_id.date', readonly=True,
    )
    advance_number = fields.Char(
        string='Número', related='advance_payment_id.nr_advance', readonly=True,
    )
    currency_id = fields.Many2one(
        'res.currency', string='Moeda', related='advance_payment_id.currency_id',
        readonly=True,
    )
    amount_total = fields.Monetary(
        string='Valor Total', related='advance_payment_id.amount', readonly=True,
        currency_field='currency_id',
    )
    amount_available = fields.Monetary(
        string='Valor Disponível', currency_field='currency_id', readonly=True,
    )
    amount_to_apply = fields.Monetary(
        string='Valor a Aplicar', currency_field='currency_id',
    )
    is_selected = fields.Boolean(string='Selecionar', default=False)
