# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from ast import literal_eval
from datetime import datetime

from odoo import fields, http, _
from odoo.exceptions import UserError, ValidationError
from odoo.http import request
from odoo.osv.expression import AND, OR
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.addons.hr_timesheet.controllers.portal import TimesheetCustomerPortal


class TimesheetCustomerPortal(TimesheetCustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super(TimesheetCustomerPortal, self)._prepare_home_portal_values(counters)
        if 'timesheet_count' in counters:
            values['timesheet_count'] = 0
            domain = request.env['account.analytic.line']._timesheet_get_portal_domain()
            employee_domain = []
            employees = request.env['hr.employee'].sudo().search(employee_domain)
            values['timesheet_count'] = request.env['account.analytic.line'].sudo().search_count(domain)
            # values['employees'] = employees
            if values['timesheet_count'] == 0:
                values['timesheet_count'] = 1
        return values

    @http.route(['/timesheet/project_infos/'], type='json', auth="user", methods=['POST'], website=True)
    def project_infos(self, project_id, **kw):
        tasks = request.env['project.task'].search_read([('project_id', '=', int(project_id))], ['id', 'name'])
        return tasks

    def _timesheet_get_page_view_values(self, timesheet, access_token, **kwargs):
        values = {
            'page_name': 'timesheet',
            'timesheet': timesheet,
        }
        return self._get_page_view_values(timesheet, access_token, values, 'my_timesheets_history', False, **kwargs)

    @http.route(['/my/timesheets', '/my/timesheets/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_timesheets(self, page=1, sortby=None, filterby=None, search=None, search_in='all', groupby='none', **kw):
        values = super(TimesheetCustomerPortal, self).portal_my_timesheets(page=page, sortby=sortby, filterby=filterby, search=search, search_in=search_in, groupby=groupby, **kw)
        employee_id = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.uid)], limit=1)

        values.qcontext.update({'employee_id': employee_id})
        return values

    @http.route(['/create/timesheet'], type='http', auth="user", website=True, csrf=False)
    def create_timesheet(self, **post):
        """
            Create and update method for timesheet.
        """
        redirect = ("/create/new/timesheet")
        try:
            # Unit Amount Cal
            hours = post.get('unit_amount_hours') or 0
            minutes = post.get('unit_amount_minutes') or 0
            unit_amount = self.convert_float(hours, minutes)

            if not post.get('task_id'):
                raise ValidationError("There is no any task is associated with this project.")
            if post.get('date'):
                GivenDate = datetime.strptime(post.get('date'), DF).date()
                if GivenDate and (GivenDate > fields.Date.today()):
                    raise UserError("Date format must be less than or equal to today's date.")
            employee_id = False
            if post.get('employee_id'):
                employee_id = literal_eval(post.get('employee_id'))

            vals = {
                'name': post.get('name'),
                'task_id': literal_eval(post.get('task_id')) or False,
                'employee_id': employee_id,
                'date': post.get('date'),
                'project_id': literal_eval(post.get('project_id')) or False,
                'unit_amount': unit_amount,
                'user_id': request.env.uid,
            }
            try:
                if post.get('timesheet_id'):
                    timesheet_id = self._document_check_access('account.analytic.line', literal_eval(post.get('timesheet_id')), access_token=False)
                    timesheet_id.check_access_rights('write')
                    timesheet_id.sudo().update(vals)
                    return request.redirect("/my/timesheet/%s" % timesheet_id.id)
                timesheet_id = request.env['account.analytic.line'].sudo().create(vals)
                return request.redirect("/my/timesheet/%s" % timesheet_id.id)
            except Exception as e:
                return request.redirect("%s?error_msg=%s" % (redirect, (str(e))))

        except Exception as e:
            return request.redirect("%s?error_msg=%s" % (redirect, (str(e))))

    @http.route(['/my/timesheet/<int:timesheet_id>'], type='http', auth="user", website=True, csrf=False)
    def portal_my_timesheet(self, timesheet_id=None, access_token=None, **kw):
        redirect = ("/my/timesheets")
        try:
            timesheet_sudo = self._document_check_access('account.analytic.line', timesheet_id, access_token)
            domain_project = [('allow_timesheets', '=', True)]
            domain_task = []
            employee_domain = []
            if request.env.user.has_group('base.group_portal'):
                domain_project = [('allow_timesheets', '=', True), ('privacy_visibility', '=', 'portal'),
                                  ('message_partner_ids', 'child_of', [request.env.user.partner_id.id])]
                domain_task = [('project_id.privacy_visibility', '=', 'portal'),
                               ('project_id.message_partner_ids', 'child_of', [request.env.user.partner_id.id])]
                employee_domain = [('user_id', '=', request.env.uid)]
            projects = request.env['project.project'].sudo().search(domain_project)
            tasks = request.env['project.task'].sudo().search(domain_task)
            employees = request.env['hr.employee'].sudo().search(employee_domain)

            values = self._timesheet_get_page_view_values(timesheet_sudo, access_token, **kw)
            values.update({
                'projects': projects,
                'employees': employees,
                'tasks': tasks
            })
            return request.render("portal_user_timesheet_access.portal_my_timesheet", values)
        except Exception as e:
            return request.redirect("%s?error_msg=%s" % (redirect, (str(e))))

    @http.route(['/my/timesheet/delete/<int:timesheet_id>'], type='http', auth="user", website=True, csrf=False)
    def portal_unlink_timesheet(self, timesheet_id=None, access_token=None, **kw):
        redirect = '/my/timesheets'
        try:
            timesheet_sudo = self._document_check_access('account.analytic.line', timesheet_id, access_token)
            if timesheet_sudo:
                timesheet_sudo.unlink()
            return request.redirect(redirect)
        except Exception as e:
            return request.redirect("%s?error_msg=%s" % (redirect, (str(e))))

    @http.route(['/create/new/timesheet'], type='http', auth="user", website=True, csrf=False)
    def portal_new_timesheet(self, access_token=None, **kw):
        redirect = '/create/new/timesheet'
        try:
            domain_project = [('allow_timesheets', '=', True)]
            domain_task = []
            employee_domain = []
            # Portal User Wise Filtered
            if request.env.user.has_group('base.group_portal'):
                domain_project = [('allow_timesheets', '=', True), ('privacy_visibility', '=', 'portal'),
                                  ('message_partner_ids', 'child_of', [request.env.user.partner_id.id])]
                domain_task = [('project_id.privacy_visibility', '=', 'portal'),
                               ('project_id.message_partner_ids', 'child_of', [request.env.user.partner_id.id])]
                employee_domain = [('user_id', '=', request.env.uid)]
            projects = request.env['project.project'].sudo().search(domain_project)
            tasks = request.env['project.task'].sudo().search(domain_task)
            employees = request.env['hr.employee'].sudo().search(employee_domain)
            values = {
                'projects': projects,
                'employees': employees,
                'tasks_data': tasks,
                'page_name': 'timesheet_creates',
                'currentDate': datetime.today().date(),
            }
            return request.render("portal_user_timesheet_access.portal_my_timesheet", values)
        except Exception as e:
            return request.redirect("%s?error_msg=%s" % (redirect, (str(e))))

    def convert_float(self, hours, minutes):
        factor = 1
        hours = int(hours)
        minutes = int(minutes)
        return factor * (hours + (minutes / 60))
