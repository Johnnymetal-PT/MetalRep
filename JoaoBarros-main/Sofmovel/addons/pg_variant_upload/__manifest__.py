{
    'name': 'PG Variant Upload with Custom Attributes',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'Import products with attributes and variants from an Excel file and manage custom product attributes',
    'depends': ['website_sale', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
    ],
    'installable': True,
    'application': False,
}
