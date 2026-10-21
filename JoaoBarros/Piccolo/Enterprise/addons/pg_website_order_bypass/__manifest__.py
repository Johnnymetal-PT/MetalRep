# __manifest__.py
{
    'name': 'PG Website Order Bypass',
    'version': '1.0',
    'category': 'Website',
    'summary': 'Bypass payment during checkout and allow order confirmation without immediate payment',
    'author': 'Your Name or Company',
    'depends': ['website_sale', 'sale', 'account'],
    'data': [
        'views/payment_acquirer.xml',
        'views/templates.xml',
    ],
    'installable': True,
    'application': False,
}
