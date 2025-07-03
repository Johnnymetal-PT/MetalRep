{
    'name': 'PG Variant Specific Pricing',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Import and update product variant prices from an Excel file.',
    'description': 'This module imports product variant prices from an Excel file and updates the list_price field.',
    'depends': ['base', 'product', 'website_sale'],
    'data': [
        'views/import_view.xml',  # Your view for importing the file
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
}
