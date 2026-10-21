# -*- coding: utf-8 -*-

from odoo import models, fields, api

class B2BApplicationRejectWizard(models.TransientModel):
    _name = 'b2b.application.reject.wizard'
    _description = 'B2B Application Rejection Wizard'

    application_id = fields.Many2one('b2b.application', string='Application', required=True)
    rejection_reason = fields.Text(string='Rejection Reason', required=True,
                                   help='Please provide a reason for rejecting this application')

    def action_confirm_reject(self):
        """Confirm rejection and update application"""
        self.ensure_one()
        if self.application_id:
            self.application_id.write({
                'state': 'rejected',
                'rejection_reason': self.rejection_reason
            })
            self.application_id._notify_applicant_status_change()
        return {'type': 'ir.actions.act_window_close'}