{
    'name': 'PG Custom Product Import Extension Kave',
    'version': '17.0.1.0.0',
    'summary': 'Extend Odoo’s default Excel import to manage product tags and archiving.',
    'author': 'Your Name',
    'depends': ['base', 'product', 'sale', 'web'],  # 'product' is needed for product.template and product.tag models
    'data': [
        'views/product_import_menu.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
}
