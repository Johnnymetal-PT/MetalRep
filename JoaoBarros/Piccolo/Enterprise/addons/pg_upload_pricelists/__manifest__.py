{
    'name': 'PG Pricelist Import Module',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Module to import pricelists from an Excel file',
    'description': 'This module allows the user to import pricelists from an Excel file and automatically update product prices based on that file.',
    'author': 'Your Name',
    'depends': ['base', 'product'],
    'data': [
        'views/pricelists_import_wizard_view.xml',
    ],
    'installable': True,
    'application': True,
}

