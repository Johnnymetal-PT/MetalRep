# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    b2b_admin_user_ids = fields.Many2many(
        'res.users',
        string='B2B Application Admins',
        help='Users who can view and approve B2B applications',
        domain=[('share', '=', False)]
    )

    b2b_terms_and_conditions = fields.Html(related='website_id.b2b_terms_and_conditions', string="Default Terms and Conditions as a B2B Signup page",
                                     readonly=False)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICP = self.env['ir.config_parameter'].sudo()

        # Get admin user ids
        admin_user_ids = ICP.get_param('b2b_application.admin_user_ids', '')
        res['b2b_admin_user_ids'] = [(6, 0, [int(uid) for uid in admin_user_ids.split(',') if uid.isdigit()])] if admin_user_ids else [(6, 0, [])]

        # Get terms and conditions
        res['b2b_terms_and_conditions'] = ICP.get_param('b2b_application.terms_and_conditions', '')

        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICP = self.env['ir.config_parameter'].sudo()

        # Set admin users
        group = self.env.ref('atharva_theme_base.group_b2b_admin', raise_if_not_found=False)
        admin_ids = ','.join(map(str, self.b2b_admin_user_ids.ids))
        ICP.set_param('b2b_application.admin_user_ids', admin_ids)

        if group:
            group.user_ids = [(6, 0, self.b2b_admin_user_ids.ids)]
        else:
            raise ValueError("Group 'atharva_theme_base.group_b2b_admin' not found!")

        # Set terms and conditions
        ICP.set_param('b2b_application.terms_and_conditions', self.b2b_terms_and_conditions or '')