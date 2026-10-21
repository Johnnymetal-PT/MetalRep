{
    'name': 'PG Variant Update',
    'version': '1.0',
    'summary': 'Updates product variants based on Excel file data',
    'author': 'Your Name',
    'category': 'Product',
    'depends': ['product'],
    'data': [
        'views/product_template_views.xml',
        'views/product_variant_update_wizard_views.xml',
        'data/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
}