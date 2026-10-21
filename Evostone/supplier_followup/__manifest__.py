# -*- coding: utf-8 -*-
{
    'name': 'Supplier Payment Follow-up Management',
    'version': '18.0.1.0',
    'category': 'Accounting/Accounting',
    'summary': 'Manage payment follow-ups for suppliers (Bills)',
    'description': """
Supplier Payment Follow-up Management
======================================

This module extends the account_followup functionality to manage payment reminders for suppliers.
It allows you to track and follow up on bills (vendor invoices) that need to be paid.

Key Features:
-------------
* Dedicated menu for supplier follow-ups
* Track overdue bills and payment schedules
* Send reminders to internal teams about pending payments
* Reuse follow-up levels from account_followup module
* Separate from customer follow-ups to avoid confusion

This module depends on account_followup to reuse the follow-up line configuration.
    """,
    'author': 'Custom Development',
    'depends': ['account_followup', 'account_reports'],
    'data': [
        'security/ir.model.access.csv',
        'security/supplier_followup_security.xml',
        'data/supplier_followup_data.xml',
        'data/supplier_followup_report.xml',
        'wizard/supplier_followup_manual_reminder_views.xml',
        'views/account_followup_line_views.xml',
        'views/res_partner_views.xml',
        'views/supplier_followup_views.xml',
        'views/account_move_views.xml',
        'views/account_journal_dashboard_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}