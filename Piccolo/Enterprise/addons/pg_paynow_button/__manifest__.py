# __manifest__.py

{
    'name': 'PG PayNow Button',
    'version': '1.0',
    'summary': 'Customizes the PayNow submit button label.',
    'description': 'This module customizes the label of the payment submit button in Odoo 17.',
    'category': 'Customization',
    'author': 'Your Name',
    'depends': ['payment'],
    'data': [
        'views/payment_template.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}

