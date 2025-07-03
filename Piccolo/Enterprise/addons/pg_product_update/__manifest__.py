{
    'name': 'PG - Product Update',
    'version': '2.0',
    'summary': 'sum',
    'description': 'Desc.',
    'author': 'Parâmetro Global',
    'license': 'LGPL-3',
    'depends': ['base', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_update_view.xml',
    ],
    'installable': True,
    'application': False,
}
