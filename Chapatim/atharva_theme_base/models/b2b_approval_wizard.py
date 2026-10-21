# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class B2BApplicationApprovalWizard(models.TransientModel):
    _name = 'b2b.application.approval.wizard'
    _description = 'B2B Application Approval Wizard'

    application_id = fields.Many2one(
        'b2b.application',
        string='B2B Application',
        required=True,
        readonly=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        readonly=True,
        help="Partner that will be created or already exists"
    )
    pricelist_id = fields.Many2one(
        'product.pricelist',
        string='Pricelist',
        required=True,
        help="Select the pricelist for this partner"
    )
    business_name = fields.Char(
        related='application_id.business_name',
        string='Business Name',
        readonly=True
    )
    email = fields.Char(
        related='application_id.email',
        string='Email',
        readonly=True
    )

    #=== DEFAULT GET METHOD ===#
    @api.model
    def default_get(self, fields_list):
        """Set default values from context"""
        res = super().default_get(fields_list)

        application_id = self.env.context.get('active_id')
        if application_id:
            application = self.env['b2b.application'].browse(application_id)
            res['application_id'] = application_id
            res['partner_id'] = application.partner_id.id if application.partner_id else False

            default_pricelist = self.env['product.pricelist'].search([], limit=1)
            if default_pricelist:
                res['pricelist_id'] = default_pricelist.id

        return res

    #=== ACTION METHODS ===#
    def action_approve(self):
        self.ensure_one()
        if not self.pricelist_id:
            raise UserError(_("Please select a pricelist before approving."))
        application = self.application_id
        application.property_product_pricelist = self.pricelist_id.id
        create_user = application._create_portal_user()
        if create_user:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('B2B Application approved successfully with pricelist: %s') % self.pricelist_id.name,
                    'type': 'success',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('User Creation Failed'),
                    'message': _('Unable to create the portal user. Please check the details and try again.'),
                    'type': 'danger',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }

    def action_cancel(self):
        """Cancel the wizard"""
        return {'type': 'ir.actions.act_window_close'}
