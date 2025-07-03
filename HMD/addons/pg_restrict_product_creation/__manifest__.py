{
    'name': 'PG Product Creation Blocklist Manager',
    'version': '17.0.1.0.0',
    'category': 'Inventory',
    'summary': 'Allows specific users to manage blocked emails for product creation',
    'author': 'Your Name',
    'depends': ['product'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
        'views/wizard_views.xml',
    ],
    'installable': True,
    'application': False,
}
