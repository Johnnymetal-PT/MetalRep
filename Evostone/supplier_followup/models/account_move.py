# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    supplier_followup_status = fields.Selection(
        related='partner_id.supplier_followup_status',
        string='Estado do Follow-up de Fornecedor',
        store=False
    )
    
    def action_post(self):
        """Override to automatically assign follow-up lines to supplier bills"""
        res = super().action_post()
        
        for move in self.filtered(lambda m: m.move_type in ('in_invoice', 'in_refund')):
            # Get the first follow-up level for new bills
            first_followup = self.env['account_followup.followup.line'].search([
                ('company_id', '=', move.company_id.id)
            ], order='delay asc', limit=1)
            
            if first_followup:
                for line in move.line_ids.filtered(
                    lambda l: l.account_id.account_type == 'liability_payable'
                ):
                    if not line.supplier_followup_line_id:
                        line.supplier_followup_line_id = first_followup
        
        return res