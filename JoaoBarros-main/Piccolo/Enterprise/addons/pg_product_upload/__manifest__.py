{
    'name': 'PG Product Upload with Custom Attributes',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'Import products with attributes and variants from an Excel file and manage custom product attributes',
    'depends': ['product'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
        'views/product_import_wizard_view.xml',
    ],
    'installable': True,
    'application': False,
}
