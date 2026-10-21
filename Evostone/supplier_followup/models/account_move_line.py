# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    supplier_followup_line_id = fields.Many2one(
        'account_followup.followup.line',
        string='Nível de Follow-up de Fornecedor',
        copy=False,
        help="O nível de follow-up para esta linha de fatura de fornecedor"
    )
    
    supplier_blocked = fields.Boolean(
        string='Excluir dos Follow-ups de Fornecedor',
        default=False,
        help='Assinale esta opção para excluir esta fatura dos follow-ups de pagamento.'
    )
    
    # Campo expected_pay_date já existe no account_followup híbrido
    # Mas caso não exista, descomente as linhas abaixo:
    # expected_pay_date = fields.Date(
    #     string='Expected Payment Date',
    #     help='Date when the payment is expected to be made to the supplier.'
    # )