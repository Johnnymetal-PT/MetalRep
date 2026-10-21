# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import models, fields, api
from odoo.osv.expression import AND


class AccountAnalyticLine(models.Model):
    _name = 'account.analytic.line'
    _inherit = ['account.analytic.line', 'portal.mixin']

    def _compute_access_url(self):
        super(AccountAnalyticLine, self)._compute_access_url()
        for timesheet in self:
            timesheet.access_url = '/my/timesheet/%s' % timesheet.id

    def convert_time(self, float_val):
        result = False
        hours, minutes = 0, 0
        if float_val:
            hours, minutes = divmod((float_val * 60), 60)
        return {'hours': int(hours), 'minutes': int(minutes)}

    def _timesheet_get_portal_domain(self):
        partner_id = self.env.user.partner_id.commercial_partner_id
        domain = ['&', '|', '|',
            ('task_id.project_id.message_partner_ids', 'child_of', [partner_id.id]),
            ('task_id.message_partner_ids', 'child_of', [partner_id.id]),
            ('task_id.project_id.message_partner_ids', 'child_of', [partner_id.id]),
            ('task_id.project_id.privacy_visibility', '=', 'portal')
        ]
        if self.env.user.has_group('base.group_portal'):
            domain = AND([domain, [('user_id', '=', self.env.uid)]])
        return domain


class Task(models.Model):
    _name = "project.task"
    _inherit = "project.task"

    @api.model
    def _default_user_ids(self):
        return self.env.context.keys() & {'default_personal_stage_type_ids', 'default_personal_stage_type_id'} and self.env.user

    user_ids = fields.Many2many('res.users', relation='project_task_user_rel', column1='task_id', column2='user_id',
        string='Assignees', context={'active_test': False}, tracking=True, default=_default_user_ids, domain="[('active', '=', True)]")