{
    'name': 'PG buy and sell by m2',
    'version': '1.0',
    'summary': 'Add fields to cut the carpet and sell by m2.',
    'description': 'Add fields to cut the carpet and sell by m2.',
    'depends': ['base', 'product', 'sale', 'purchase', 'website', 'website_sale'],  # Added website dependencies
    'data': [
        'views/template.xml',
        'views/website_template.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}

