# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountFollowUpFollowUpLine(models.Model):
    _inherit = 'account_followup.followup.line'

    supplier_mail_template_id = fields.Many2one(
        'mail.template',
        string='Modelo de Email para Fornecedor',
        domain="[('model', '=', 'res.partner')]",
        help='Modelo de email específico para follow-up de fornecedores',
        ondelete='set null'
    )
    
    supplier_sms_template_id = fields.Many2one(
        'sms.template',
        string='Modelo de SMS para Fornecedor',
        domain="[('model', '=', 'res.partner')]",
        help='Modelo de SMS específico para follow-up de fornecedores',
        ondelete='set null'
    )