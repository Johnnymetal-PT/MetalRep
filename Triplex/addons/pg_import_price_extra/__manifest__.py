{
    'name': 'PTAV Price Extra Import',
    'version': '1.0',
    'category': 'Product',
    'depends': ['base', 'product'],
    'data': [
        'views/ptav_price_import_view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
}
