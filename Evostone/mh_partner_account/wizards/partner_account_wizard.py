# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PartnerAccountConfirmWizard(models.TransientModel):
    """Wizard simples para confirmar criação de contas"""
    _name = 'partner.account.confirm.wizard'
    _description = 'Confirmar Criação de Conta de Parceiro'

    partner_id = fields.Many2one(
        'res.partner',
        string='Parceiro',
        required=True,
        readonly=True
    )

    partner_name = fields.Char(
        related='partner_id.name',
        readonly=True
    )

    is_customer = fields.Boolean(
        compute='_compute_partner_type'
    )

    is_supplier = fields.Boolean(
        compute='_compute_partner_type'
    )

    message = fields.Char(
        compute='_compute_partner_type'
    )

    @api.depends('partner_id')
    def _compute_partner_type(self):
        for wizard in self:
            wizard.is_customer = wizard.partner_id.customer_rank > 0
            wizard.is_supplier = wizard.partner_id.supplier_rank > 0

            if wizard.is_customer and wizard.is_supplier:
                wizard.message = _("Serão criadas as contas de Cliente e Fornecedor.")
            elif wizard.is_customer:
                wizard.message = _("Será criada a conta de Cliente.")
            elif wizard.is_supplier:
                wizard.message = _("Será criada a conta de Fornecedor.")
            else:
                wizard.message = ""

    def action_confirm(self):
        """Confirmar e criar as contas"""
        self.ensure_one()
        self.partner_id.action_confirm_create_accounts()
        return {'type': 'ir.actions.act_window_close'}

    def action_cancel(self):
        """Cancelar - não criar contas"""
        self.ensure_one()
        self.partner_id.action_skip_create_accounts()
        return {'type': 'ir.actions.act_window_close'}
