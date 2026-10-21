# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

{
    'name': "Portal Expense",
    'summary': """Portal users can submit and track expense reimbursement requests.""",
    'description': """This module allows portal users to manage their expense reimbursements directly from the website portal. 
        Employees can easily create, submit, and monitor expense requests without needing back-end access, 
        streamlining the reimbursement process and improving transparency.""",
    'author': 'TechEmpyre',
    'category': 'HR',
    'version': '18.0.0.1',
    'depends': ['portal', 'hr_expense'],
    'data': [
        'security/ir.model.access.csv',
        'security/hr_expense_security.xml',
        'views/hr_res_user_view.xml',
        'views/portal_expense_request_my_account.xml',
        'views/portal_expense_template_view.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            '/portal_users_expense/static/src/js/portal_expense.js',
            '/portal_users_expense/static/src/scss/portal_expense.scss',
        ],
    },
    'images': ['static/description/main_screen.png'],
    'license': 'OPL-1',
    'currency': 'USD',
    'price': 25,
    'installable': True,
    'application': True,
    'auto_install': False,
}
