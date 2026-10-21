# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

import base64
from operator import itemgetter
from odoo import http, tools, fields, _
from odoo.http import request
from odoo.osv.expression import OR
from odoo.exceptions import ValidationError
from odoo.tools import groupby as groupbyelem
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager


class ExpensePortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super(ExpensePortal, self)._prepare_home_portal_values(counters)
        # values['expense_count'] = 0
        if 'expense_count' in counters:
            domain = []
            expense_obj = request.env['hr.expense'].sudo()
            employee_id = request.env.user.employee_id
            if employee_id:
                domain = [('employee_id', '=', request.env.user.employee_id.id)]
                values['expense_count'] = expense_obj.search_count(domain)
            # values['page_name'] = 'expense'
        values['expense_count'] = 1
        return values

    @http.route(['/my/expense', '/my/expense/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_expense(self, page=1, access_token=None, search=None, search_in='all', sortby=None, groupby='none', **kw):
        values = self._prepare_portal_layout_values()
        expense_obj = request.env['hr.expense'].with_user(request.env.uid).sudo()

        domain, expense_ids = [], expense_obj

        if request.env.user.sudo().has_group('base.group_portal') and request.env.user.employee_id:
            domain = [('employee_id', '=', request.env.user.employee_id.id)]

        searchbar_sortings = {
            'name': {'label': _('Name'), 'order': 'name asc'},
            'state': {'label': _('Status'), 'order': 'state desc'},
        }

        searchbar_inputs = {
            'all': {'input': 'all', 'label': _('Search in All')},
            'description': {'input': 'description', 'label': _('Search in Internal Notes')},
            'name': {'input': 'name', 'label': _('Search in Description')},
        }

        searchbar_groupby = {
            'none': {'input': 'none', 'label': _('None')},
            'state': {'input': 'state', 'label': _('Status')},
            'product_id': {'input': 'product_id', 'label': _('Product')},
        }

        if not sortby:
            sortby = 'name'
        order = searchbar_sortings[sortby]['order']

        # count for pager
        expense_count = expense_obj.search_count(domain)

        # search
        if search and search_in:
            search_domain = []
            if search_in in ('name', 'all'):
                search_domain = OR([search_domain, [('name', 'ilike', search)]])
            if search_in in ('description', 'all'):
                search_domain = OR([search_domain, [('description', 'ilike', search)]])
            domain += search_domain

        pager = portal_pager(
            url="/my/expense",
            total=expense_count,
            page=page,
            url_args={'search_in': search_in, 'search': search},
            step=12
        )

        grouped_expense = []
        # content according to pager and archive selected
        expense_ids = expense_obj.search(domain,  order=order, limit=12, offset=pager['offset'])
        request.session['my_expense_history'] = expense_ids.ids[:100]
        grouped_expense = [expense_ids]
        if groupby == 'state':
            grouped_expense = [expense_obj.concat(*g) for k, g in groupbyelem(expense_ids, itemgetter('state'))]
        elif groupby == 'product_id':
            grouped_expense = [expense_obj.concat(*g) for k, g in groupbyelem(expense_ids, itemgetter('product_id'))]

        values.update({
            'expense_ids': expense_ids,
            'page_name': 'expense',
            'pager': pager,
            'default_url': '/my/expense',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'search_in': search_in,
            'groupby': groupby,
            'search': search,
            'grouped_expense': grouped_expense,
            'searchbar_inputs': searchbar_inputs,
            'searchbar_groupby': searchbar_groupby
        })
        return request.render("portal_users_expense.portal_my_expense", values)

    @http.route('/my/expense/<int:expense>', type='http', auth="user", website=True)
    def portal_my_expense_details(self, expense, access_token=None, **kw):
        try:
            expense_sudo = self._document_check_access('hr.expense', expense, access_token)
            kw['expense'] = expense_sudo
            kw['group_analytic_accounting'] = request.env.user.has_groups('analytic.group_analytic_accounting')
            kw['expense_products'] = request.env['product.product'].search([('can_be_expensed', '=', True)])
            kw['analytic_accounts'] = request.env['account.analytic.account'].search(['|', ('company_id', '=', False), ('company_id', '=', request.env.user.company_id.id)])
            kw['payment_type'] = request.env['hr.expense'].sudo()._fields['payment_mode']._description_selection(request.env)
            history = request.session.get('my_expense_history', [])
            kw.update(get_records_pager(history, expense_sudo))
            return request.render("portal_users_expense.portal_expense", kw)
        except Exception as e:
            request.env.cr.rollback()
            return request.redirect("/my/expense?error=%s" % e.args[0])

    @http.route('/onchange/product', type='json', auth='user')
    def onchnage_product(self, product_id, **kw):
        if product_id:
            product = request.env['product.product'].sudo().browse(int(product_id))
        return {'unit_price': product.list_price}

    @http.route('/create/expense/request', type='http', auth='user', website=True, csrf=False)
    def expense_request_form(self, create_from_header=None, **kw):
        try:
            employee_id = request.env.user.employee_id
            if employee_id:
                kw['employee_id'] = employee_id
            kw.update({
                'page_name': 'expense_create',
                'expense': False,
                'current_date': fields.Date.today(),
                'group_analytic_accounting': request.env.user.has_groups('analytic.group_analytic_accounting'),
                'expense_products': request.env['product.product'].search([('can_be_expensed', '=', True)]),
                'payment_type': request.env['hr.expense'].sudo()._fields['payment_mode']._description_selection(request.env),
                'analytic_accounts': request.env['account.analytic.account'].search(['|', ('company_id', '=', False), ('company_id', '=', request.env.user.company_id.id)]),
            })
            if create_from_header:
                kw['create_from_header'] = True
            return request.render("portal_users_expense.portal_expense", kw)
        except Exception as e:
            request.env.cr.rollback()
            return request.redirect("/create/expense/request?error=%s" % e.args[0])

    def create_expense_record(self, post):
        employee_id = request.env.user.employee_id
        if not employee_id:
            raise ValidationError(_('Employee not find please set your employee first.'))
        if employee_id and not post.get('expense'):
            post.update({
                'employee_id': employee_id.id,
                'product_id': int(post.get('product_id'))
            })
        if 'message' in post.keys():
            post.pop("message")
        if 'price_unit' in post.keys():
            post['price_unit'] = int(post.get('price_unit', 0))
        print("?????????????????post\n\n\n\n", post)
        return post

    def create_expense_sheet(self, expense):
        if expense and expense[0]:
            hr_expense_sheet_obj = request.env['hr.expense.sheet'].with_user(request.env.uid).sudo()
            todo = expense.filtered(lambda x: x.payment_mode=='own_account')
            expense_sheet_vals = {
                'name': todo[0].name if len(todo) == 1 else '',
                'employee_id': expense[0].employee_id.id,
                'payment_mode': 'own_account'
            }
            hr_expense_sheet_id = hr_expense_sheet_obj.create(expense_sheet_vals)
            # hr_expense_sheet_id.action_submit_sheet()
            expense.sheet_id = hr_expense_sheet_id.id

    @http.route('/expense/request', type='http', auth='public', website=True)
    def expense_request(self, **post):
        expense_id, attached_files = False, []
        try:
            expense_obj = request.env['hr.expense'].with_user(request.env.uid).sudo()
            if post.get('expense'):
                expense_id = expense_obj.browse(int(post['expense']))
            if post.get('analytic_account_id'):
                post['analytic_account_id'] = int(post['analytic_account_id'])
            if post.get('product_id'):
                post['product_id'] = int(post['product_id'])
            if expense_id:
                if len(post) > 1:
                    post = self.create_expense_record(post)
                    attached_files = request.httprequest.files.getlist('ufile')
                    self.create_document(attached_files, expense_id)
                    for value in ['expense', 'ufile']:
                        post.pop(value)
                    record = expense_id.write(post)
                    if record:
                        self.create_document(attached_files, expense_id)
                        expense_id.sudo().update_account_details()
                        self.create_expense_sheet(expense=expense_id)
                        return request.render("portal_users_expense.thankyou_expense", {'record': expense_id})
            else:
                if len(post) > 1:
                    post = self.create_expense_record(post)
                    attached_files = request.httprequest.files.getlist('ufile')
                    for value in ['expense', 'ufile']:
                        post.pop(value)
                    record = expense_obj.create(post)
                    record.price_unit = post.get('price_unit', 0)
                    print("??????????????record\n\n\n", record, record.price_unit, post)
                    if record:
                        self.create_document(attached_files, record)
                        record.sudo().update_account_details()
                        self.create_expense_sheet(expense=record)
                        return request.render("portal_users_expense.thankyou_expense", {'record': record})
        except Exception as e:
            request.env.cr.rollback()
            if not expense_id:
                return request.redirect("/create/expense/request?error=%s" % e.args[0])
            else:
                return request.redirect("/my/expense/%s?error=%s" % (expense_id.id, e.args[0]))

    # def get_employee(self):
    #     return request.env['hr.employee'].sudo().search([('user_id', '=', request.env.uid)], limit=1)

    def create_document(self, attached_files, expense_id):
        for file in attached_files:
            ufile = file.read()
            vals = {
                'res_model': 'hr.expense',
                'res_id': expense_id,
                'datas': base64.b64encode(ufile),
                'type': 'binary',
                'name': file.filename
            }
            if file.filename:
                attachment_id = request.env['ir.attachment'].sudo().create(vals)

    @http.route(['/my/expense/delete/<int:expense_id>'], type='http', auth="user", website=True)
    def portal_unlink_expense(self, expense_id=None, access_token=None, **kw):
        Expense = request.env['hr.expense'].sudo()
        redirect = '/my/expense'
        try:
            expense_sudo = self._document_check_access('hr.expense', expense_id, access_token)
            if expense_sudo:
                expense_sudo.unlink()
            return request.redirect(redirect)
        except Exception as e:
            return request.redirect("%s?error_msg=%s" % (redirect, (Expense.error_msg(e))))
