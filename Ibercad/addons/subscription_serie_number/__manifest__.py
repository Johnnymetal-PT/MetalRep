{
    'name': 'pg_Subscription_Number',
    'version': '1.0',
    'depends': ['base', 'sale' , 'account', 'sale_subscription'],
    'data': [
        'views/number_on_sale.xml',
        'views/display_invoice.xml',
        'reports/invoice_reports.xml',
        'reports/pdf_quotes.xml',
    ],

    'installable': True,
    'application': False,
}