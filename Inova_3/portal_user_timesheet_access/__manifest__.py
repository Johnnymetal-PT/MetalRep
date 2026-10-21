# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

{
    'name': 'Portal User TimeSheet Management',
    'version': '1.0',
    'summary': 'Enable portal users to log, manage, and view their timesheets with full control and transparency directly from the Odoo portal.',
    'sequence': 20,
    'description': """
        Portal User Timesheet Management is a powerful Odoo module that extends the functionality of the portal to allow external users (portal users) to effectively manage their timesheets. This module is ideal for companies working with freelancers, contractors, or external collaborators who need to submit or track work hours without full backend access.

        Portal Timesheet Entry
        Customizable Access Rights
        Project
        User
        Task
        HR
        Employee
        Portal timesheet
        Responsive Portal UI
        timesheet
        Portal
        Timesheet Review
        Project and Task Linking
        Time sheet
    """,
    'category': 'Project',
    'author': 'TechEmpyre',
    'depends': ['portal', 'hr_timesheet'],
    'data': [
        'security/ir.model.access.csv',
        'security/timesheet_security.xml',
        'views/res_user_view.xml',
        'views/timesheet_portal_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            '/portal_user_timesheet_access/static/src/js/timesheet.js',
        ],
    },
    'price': 25,
    'currency': 'USD',
    'images': ['static/description/main_screen.png'],
    'license': 'OPL-1',
    'installable': True,
    'application': True,
    'auto_install': False,
}
