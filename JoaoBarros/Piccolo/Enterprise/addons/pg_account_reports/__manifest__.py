{
    'name': 'PG Account Report Enhancements',
    'version': '17.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Adds Days Overdue column to Aged Partner Balance Reports',
    'author': 'Parâmetro Global',
    'depends': ['account_reports'],
    'data': [
        'views/account_aged_report_extension.xml',
        'views/account_partner_ledger_extension.xml',
    ],
    'installable': True,
}
